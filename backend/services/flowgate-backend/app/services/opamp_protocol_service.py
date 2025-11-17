"""OpAMP Protocol Service - Handles OpAMP Protobuf messages

Implements OpAMP protocol message handling according to:
https://opentelemetry.io/docs/specs/opamp/
"""

from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.services.opamp_service import OpAMPService
from app.services.gateway_service import GatewayService
from app.services.opamp_config_service import OpAMPConfigService
from app.models.gateway import OpAMPRemoteConfigStatus, ManagementMode
from app.services.opamp_capabilities import (
    AgentCapabilities,
    ServerCapabilities,
    negotiate_capabilities
)
from app.services.opamp_supervisor_service import OpAMPSupervisorService
from app.services.package_service import PackageService
from app.services.connection_settings_service import ConnectionSettingsService
from app.models.agent_package import PackageStatus
from app.models.connection_settings import ConnectionSettingsStatus
from app.protobufs import opamp_pb2
from app.services.opamp_go_parser import get_go_parser
import logging

logger = logging.getLogger(__name__)


def bytes_to_hash_str(value: Union[bytes, str, None]) -> Optional[str]:
    """
    Safely convert bytes returned by OpAMP (typically hashes) into a printable string.
    Hashes are arbitrary bytes, so attempt hex encoding first to avoid UnicodeDecodeError.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            # Many agents already send ASCII hash strings; try decoding first for readability
            decoded = value.decode("utf-8")
            return decoded
        except UnicodeDecodeError:
            return value.hex()
    return str(value)


def infer_component_type(component_id: str) -> str:
    """
    Infer component type from component_id naming patterns.
    
    Args:
        component_id: Component identifier (e.g., "otlp/receiver", "batchprocessor")
        
    Returns:
        Component type: 'receiver', 'processor', 'exporter', 'extension', or 'unknown'
    """
    component_id_lower = component_id.lower()
    
    # Check for explicit type indicators
    if '/receiver' in component_id_lower or component_id_lower.endswith('receiver'):
        return 'receiver'
    elif '/processor' in component_id_lower or component_id_lower.endswith('processor'):
        return 'processor'
    elif '/exporter' in component_id_lower or component_id_lower.endswith('exporter'):
        return 'exporter'
    elif '/extension' in component_id_lower or component_id_lower.endswith('extension'):
        return 'extension'
    
    return 'unknown'


def parse_component_details(component_details, component_id: str) -> Dict[str, Any]:
    """
    Parse ComponentDetails protobuf message to dictionary.
    
    Args:
        component_details: ComponentDetails protobuf message
        component_id: Component identifier
        
    Returns:
        Dictionary with parsed component information
    """
    result = {
        "component_id": component_id,
        "name": component_id.split('/')[-1] if '/' in component_id else component_id,
        "component_type": infer_component_type(component_id),
        "metadata": {},
        "sub_components": []
    }
    
    # Parse metadata from KeyValue pairs
    if component_details.metadata:
        for kv in component_details.metadata:
            # In proto3, string fields don't have presence - check if non-empty
            if kv.key and kv.HasField("value"):
                # Extract value from AnyValue
                if kv.value.HasField("string_value"):
                    result["metadata"][kv.key] = kv.value.string_value
                elif kv.value.HasField("int_value"):
                    result["metadata"][kv.key] = kv.value.int_value
                elif kv.value.HasField("bool_value"):
                    result["metadata"][kv.key] = kv.value.bool_value
                elif kv.value.HasField("double_value"):
                    result["metadata"][kv.key] = kv.value.double_value
                else:
                    result["metadata"][kv.key] = str(kv.value)
    
    # Extract common metadata fields
    if "version" in result["metadata"]:
        result["version"] = result["metadata"]["version"]
    
    # Extract supported data types
    supported_types = []
    if result["metadata"].get("metrics") or result["metadata"].get("supports_metrics"):
        supported_types.append("metrics")
    if result["metadata"].get("logs") or result["metadata"].get("supports_logs"):
        supported_types.append("logs")
    if result["metadata"].get("traces") or result["metadata"].get("supports_traces"):
        supported_types.append("traces")
    if supported_types:
        result["supported_data_types"] = supported_types
    
    # Extract stability
    stability = result["metadata"].get("stability") or result["metadata"].get("status")
    if stability:
        stability_lower = str(stability).lower()
        if "stable" in stability_lower:
            result["stability"] = "stable"
        elif "experimental" in stability_lower or "beta" in stability_lower:
            result["stability"] = "experimental"
        elif "deprecated" in stability_lower:
            result["stability"] = "deprecated"
    
    # Parse sub-components recursively
    if component_details.sub_component_map:
        for sub_id, sub_details in component_details.sub_component_map.items():
            sub_component = parse_component_details(sub_details, sub_id)
            result["sub_components"].append(sub_component)
    
    return result


class OpAMPProtocolService:
    """Service for handling OpAMP protocol messages"""
    
    def __init__(self, db: Session):
        self.db = db
        self.opamp_service = OpAMPService(db)
        self.gateway_service = GatewayService(db)
        self.config_service = OpAMPConfigService(db)
        self.supervisor_service = OpAMPSupervisorService(db)
        self.package_service = PackageService(db)
        self.connection_settings_service = ConnectionSettingsService(db)
    
    def process_agent_to_server(
        self,
        instance_id: str,
        message: opamp_pb2.AgentToServer
    ) -> opamp_pb2.ServerToAgent:
        """
        Process AgentToServer message and return ServerToAgent response
        
        Args:
            instance_id: Gateway instance identifier
            message: Parsed AgentToServer message (dict representation)
        
        Returns:
            ServerToAgent message (dict representation)
        """
        logger.info(f"[OpAMP] Processing AgentToServer message from {instance_id}")
        logger.info(f"[OpAMP] Message details: seq={message.sequence_num}, capabilities=0x{message.capabilities:X}, has_effective_config={message.HasField('effective_config')}, has_remote_config_status={message.HasField('remote_config_status')}, has_health={message.HasField('health')}, has_agent_description={message.HasField('agent_description')}, has_package_statuses={message.HasField('package_statuses')}, has_connection_settings_status={message.HasField('connection_settings_status')}, has_available_components={message.HasField('available_components')}")
        
        # Get gateway
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if not gateway:
            raise ValueError(f"Gateway not found: {instance_id}")
        
        logger.info(f"[OpAMP] Gateway {instance_id} found: connection_status={gateway.opamp_connection_status}, agent_capabilities=0x{gateway.opamp_agent_capabilities or 0:X}, has_effective_config_content={bool(gateway.opamp_effective_config_content)}")
        
        # Update heartbeat
        self.gateway_service.update_heartbeat(instance_id)
        
        # Extract and store OpAMP-specific data from message
        # Extract sequence number (uint64, always present in proto3, defaults to 0)
        # In proto3, scalar fields don't have presence, so we can't use HasField()
        # sequence_num will be 0 if not set, which is valid
        sequence_num = message.sequence_num
        if sequence_num > 0:  # Only update if non-zero (0 means not set or first message)
            self.gateway_service.update_opamp_sequence_num(instance_id, sequence_num)
        
        # Extract agent capabilities (uint64, always present, defaults to 0)
        agent_capabilities = message.capabilities
        
        # Log raw capabilities for debugging - always at INFO level to track what's being sent
        logger.info(f"[OpAMP] Agent {instance_id} raw capabilities from message: 0x{agent_capabilities:X} ({agent_capabilities})")
        
        # Decode capabilities immediately to see what's actually being sent
        if agent_capabilities > 0:
            decoded_capabilities = AgentCapabilities.decode_capabilities(agent_capabilities)
            logger.info(f"[OpAMP] Agent {instance_id} decoded capabilities: {', '.join(decoded_capabilities)}")
        else:
            logger.warning(f"[OpAMP] Agent {instance_id} reported ZERO capabilities (0x0) - this may indicate a problem")
        
        # If supervisor reports 0 capabilities, infer from supervisor.yaml configuration
        # This is a workaround for supervisor not properly reading/reporting capabilities
        # The supervisor reads capabilities from supervisor.yaml and should report them, but sometimes reports 0x0
        # Reference: 
        # - Supervisor config: https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/cmd/opampsupervisor/supervisor/config/config.go
        # - Extension code: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/extension/opampextension
        if agent_capabilities == 0 and gateway.management_mode == ManagementMode.SUPERVISOR.value:
            logger.warning(
                f"Agent {instance_id} (supervisor mode) reported capabilities as 0x0 - "
                f"inferring from supervisor.yaml configuration. "
                f"This may indicate the supervisor is not properly reading or reporting capabilities."
            )
            
            # Calculate expected capabilities based on supervisor.yaml configuration
            # Per supervisor config.go, these are the configurable capabilities:
            # - accepts_remote_config, reports_remote_config, reports_effective_config
            # - reports_own_metrics, reports_own_logs, reports_own_traces
            # - reports_health, reports_heartbeat
            # - accepts_opamp_connection_settings, reports_available_components
            # - accepts_restart_command
            # Plus automatic: reports_status (always enabled in supervisor's SupportedCapabilities())
            # Note: supervisor does NOT support: accepts_packages, reports_package_statuses,
            #       accepts_other_connection_settings, reports_connection_settings_status
            
            # Define expected capabilities based on supervisor.yaml configuration
            expected_capabilities_set = {
                AgentCapabilities.REPORTS_STATUS,  # Always enabled (hardcoded in supervisor)
                AgentCapabilities.ACCEPTS_REMOTE_CONFIG,  # From supervisor.yaml
                AgentCapabilities.REPORTS_EFFECTIVE_CONFIG,  # From supervisor.yaml
                AgentCapabilities.REPORTS_REMOTE_CONFIG,  # From supervisor.yaml
                AgentCapabilities.REPORTS_OWN_METRICS,  # From supervisor.yaml
                AgentCapabilities.REPORTS_OWN_LOGS,  # From supervisor.yaml
                AgentCapabilities.REPORTS_OWN_TRACES,  # From supervisor.yaml
                AgentCapabilities.REPORTS_HEALTH,  # From supervisor.yaml
                AgentCapabilities.REPORTS_HEARTBEAT,  # From supervisor.yaml
                AgentCapabilities.ACCEPTS_OPAMP_CONNECTION_SETTINGS,  # From supervisor.yaml
                AgentCapabilities.REPORTS_AVAILABLE_COMPONENTS,  # From supervisor.yaml
                AgentCapabilities.ACCEPTS_RESTART_COMMAND,  # From supervisor.yaml
            }
            
            # Calculate bit-field from expected capabilities
            inferred_capabilities = AgentCapabilities.to_bit_field(expected_capabilities_set)
            agent_capabilities = inferred_capabilities
            
            # Decode and log inferred capabilities for verification
            decoded_capabilities = AgentCapabilities.decode_capabilities(inferred_capabilities)
            logger.info(
                f"[OpAMP] Inferred capabilities for supervisor-managed agent {instance_id}: "
                f"0x{inferred_capabilities:X} ({inferred_capabilities}) - "
                f"Capabilities: {', '.join(decoded_capabilities)}"
            )
            
            # Verify the inferred capabilities match expected set
            actual_capabilities_set = AgentCapabilities.from_bit_field(inferred_capabilities)
            if actual_capabilities_set != expected_capabilities_set:
                missing = expected_capabilities_set - actual_capabilities_set
                extra = actual_capabilities_set - expected_capabilities_set
                if missing:
                    logger.warning(f"Missing expected capabilities: {[AgentCapabilities.NAMES.get(c, f'Unknown({c})') for c in missing]}")
                if extra:
                    logger.warning(f"Unexpected extra capabilities: {[AgentCapabilities.NAMES.get(c, f'Unknown({c})') for c in extra]}")
        elif agent_capabilities == 0:
            # Agent reported 0 capabilities but is not in supervisor mode
            logger.warning(
                f"Agent {instance_id} (mode: {gateway.management_mode}) reported capabilities as 0x0 - "
                f"may not be properly configured. "
                f"Expected capabilities should be reported by the OpAMP extension or supervisor."
            )
        else:
            # Agent reported non-zero capabilities - decode and log them
            decoded_capabilities = AgentCapabilities.decode_capabilities(agent_capabilities)
            logger.info(
                f"[OpAMP] Agent {instance_id} reported capabilities: "
                f"0x{agent_capabilities:X} ({agent_capabilities}) - "
                f"Capabilities: {', '.join(decoded_capabilities)}"
            )
        
        # Decode capabilities once for re-use
        agent_caps = AgentCapabilities.from_bit_field(agent_capabilities)

        # Store agent and server capabilities
        server_capabilities = ServerCapabilities.get_all_capabilities()
        
        # Log what we're storing
        logger.info(
            f"[OpAMP] Storing capabilities for {instance_id}: "
            f"agent=0x{agent_capabilities:X} ({agent_capabilities}), "
            f"server=0x{server_capabilities:X} ({server_capabilities})"
        )
        
        self.gateway_service.update_opamp_capabilities(
            instance_id,
            agent_capabilities=agent_capabilities,
            server_capabilities=server_capabilities
        )
        
        # Verify what was stored
        gateway_after = self.gateway_service.repository.get_by_instance_id(instance_id)
        if gateway_after:
            logger.info(
                f"[OpAMP] Verified stored capabilities for {instance_id}: "
                f"agent=0x{gateway_after.opamp_agent_capabilities or 0:X}, "
                f"server=0x{gateway_after.opamp_server_capabilities or 0:X}"
            )
        
        # Extract remote config status and update audit log
        if message.HasField("remote_config_status"):
            remote_config_status = message.remote_config_status
            logger.info(f"[OpAMP] Agent {instance_id} remote_config_status received:")
            logger.info(f"  - status: {remote_config_status.status}")
            # In proto3, bytes and string fields don't have presence - check if non-empty instead
            hash_bytes = remote_config_status.last_remote_config_hash
            hash_str = bytes_to_hash_str(hash_bytes)
            logger.info(f"  - last_remote_config_hash: {hash_str if hash_str else 'not set (empty)'}")
            error_msg = remote_config_status.error_message if remote_config_status.error_message else None
            logger.info(f"  - error_message: {error_msg if error_msg else 'not set (empty)'}")
            # Map OpAMP protobuf enum to our model enum
            status_mapping = {
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_UNSET: OpAMPRemoteConfigStatus.UNSET,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED: OpAMPRemoteConfigStatus.APPLIED,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLYING: OpAMPRemoteConfigStatus.APPLYING,
                opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_FAILED: OpAMPRemoteConfigStatus.FAILED,
            }
            opamp_status = status_mapping.get(
                remote_config_status.status,
                OpAMPRemoteConfigStatus.UNSET
            )
            self.gateway_service.update_opamp_remote_config_status(instance_id, opamp_status)
            
            # Store config hash if present and update audit log
            if remote_config_status.last_remote_config_hash:
                hash_bytes = remote_config_status.last_remote_config_hash
                try:
                    hash_str = bytes_to_hash_str(hash_bytes)
                    self.gateway_service.update_opamp_config_hashes(
                        instance_id,
                        effective_config_hash=None,  # Will be set from effective_config if present
                        remote_config_hash=hash_str
                    )
                    
                    # Get effective config hash if present
                    effective_hash = None
                    if message.HasField("effective_config") and message.effective_config.hash:
                        eff_hash_bytes = message.effective_config.hash
                        try:
                            effective_hash = bytes_to_hash_str(eff_hash_bytes)
                        except (ValueError, AttributeError):
                            pass
                    
                    # Update config status in audit log
                    status_str = opamp_status.value if opamp_status else 'UNSET'
                    # In proto3, string fields don't have presence - check if non-empty instead
                    error_msg = remote_config_status.error_message if remote_config_status.error_message else None
                    
                    self.config_service.update_config_status_from_agent(
                        instance_id=instance_id,
                        config_hash=hash_str,
                        status=status_str,
                        effective_config_hash=effective_hash,
                        error_message=error_msg
                    )
                except (ValueError, AttributeError):
                    pass
        
        # Extract effective config hash if present
        # Check for effective_config in message
        has_effective_config = message.HasField("effective_config")
        logger.info(f"[OpAMP] Checking effective_config for {instance_id}: has_field={has_effective_config}")
        if has_effective_config:
            effective_config = message.effective_config
            logger.info(f"[OpAMP] Agent {instance_id} effective_config received:")
            # EffectiveConfig only has config_map field (no hash field)
            if effective_config.HasField("config_map"):
                logger.info(f"  - config_map files count: {len(effective_config.config_map.config_map)}")
                for file_name in effective_config.config_map.config_map.keys():
                    logger.info(f"    - config file: {file_name}")
            else:
                logger.info(f"  - config_map: not set")
        else:
            logger.warning(f"[OpAMP] Agent {instance_id} did NOT send effective_config in this message")
        
        # Note: The supervisor may only send effective_config when:
        # 1. The collector is fully running and has loaded a config
        # 2. The config has changed since last report
        # 3. ReportFullState flag is set AND collector is ready AND supervisor forwards the flag
        # If has_effective_config is False, it may indicate:
        #   - The collector isn't running yet
        #   - The supervisor isn't forwarding ReportFullState flag to collector extension
        #   - The collector extension isn't responding to ReportFullState flag
        #   - Known bug in OpAMP extension (issue #29117)
        #
        # IMPORTANT: Known limitation in OpAMP extension (issue #29117):
        # The effective_config reported by the OpAMP extension may be INCOMPLETE.
        # Some components (e.g., debug exporters, telemetry service settings) may be missing.
        # Reference: https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117
        # The reported effective_config should be treated as a partial view, not the complete config.
        #
        # NOTE: In supervisor mode, the supervisor acts as a proxy. The ReportFullState flag
        # must be forwarded by the supervisor to the collector's OpAMP extension. If the supervisor
        # doesn't forward this flag, the collector extension won't know to send effective_config.
        if has_effective_config:
            effective_config = message.effective_config
            has_hash = bool(effective_config.hash) if hasattr(effective_config, 'hash') else False
            # effective_config.config_map is an AgentConfigMap message, not a dict
            # The actual map is at effective_config.config_map.config_map
            has_config_map = bool(effective_config.config_map and effective_config.config_map.config_map) if effective_config.config_map else False
            config_map_size = len(effective_config.config_map.config_map) if (effective_config.config_map and effective_config.config_map.config_map) else 0
            logger.info(f"[OpAMP] Agent {instance_id} sent effective_config: has_hash={has_hash}, has_config_map={has_config_map}, config_map_size={config_map_size}")
            
            if effective_config.config_map and effective_config.config_map.config_map:
                # Extract effective config hash
                effective_hash = None
                if hasattr(effective_config, 'hash') and effective_config.hash:
                    effective_hash_bytes = effective_config.hash
                    try:
                        effective_hash = bytes_to_hash_str(effective_hash_bytes)
                    except (ValueError, AttributeError):
                        pass
                
                # Extract effective config content (YAML) from config_map
                effective_config_yaml = None
                # OpAMP config_map is a map of filename -> ConfigFile
                # Typically contains a single entry with empty string key for the main config
                config_files = []
                for filename, config_file in effective_config.config_map.config_map.items():
                    if hasattr(config_file, 'body') and config_file.body:
                        try:
                            # ConfigFile.body is bytes, decode to string
                            config_content = config_file.body.decode('utf-8') if isinstance(config_file.body, bytes) else str(config_file.body)
                            if filename:
                                config_files.append(f"# File: {filename}\n{config_content}")
                            else:
                                config_files.append(config_content)
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.warning(f"Failed to decode effective config file {filename}: {e}")
                
                # Combine all config files (if multiple) or use the main one
                if config_files:
                    effective_config_yaml = "\n---\n".join(config_files) if len(config_files) > 1 else config_files[0]
                    logger.info(f"[OpAMP] Extracted effective config content for agent {instance_id}: {len(effective_config_yaml)} bytes, {len(config_files)} file(s)")
                    # Warn about known limitation: effective_config may be incomplete
                    # Reference: https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117
                    logger.warning(
                        f"[OpAMP] NOTE: Effective config from agent {instance_id} may be incomplete. "
                        f"Some components (e.g., debug exporters, telemetry settings) may be missing. "
                        f"See https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/29117"
                    )
                else:
                    logger.warning(f"[OpAMP] Agent {instance_id} sent effective_config with config_map but no valid config files extracted")
                
                # Update both hash and content
                if effective_hash or effective_config_yaml:
                    self.gateway_service.update_opamp_config_hashes(
                        instance_id,
                        effective_config_hash=effective_hash,
                        remote_config_hash=None,  # Don't overwrite if already set
                        effective_config_content=effective_config_yaml
                    )
                    if effective_config_yaml:
                        logger.debug(f"Stored effective config content for agent {instance_id} (hash: {effective_hash})")
                    
                    # Update pending ConfigRequest records for this instance
                    try:
                        from app.models.config_request import ConfigRequest, ConfigRequestStatus
                        pending_requests = self.db.query(ConfigRequest).filter(
                            ConfigRequest.instance_id == instance_id,
                            ConfigRequest.status == ConfigRequestStatus.PENDING
                        ).all()
                        
                        logger.info(f"[OpAMP] Found {len(pending_requests)} pending ConfigRequest(s) for {instance_id}, updating to completed")
                        for config_request in pending_requests:
                            config_request.status = ConfigRequestStatus.COMPLETED
                            config_request.effective_config_content = effective_config_yaml
                            config_request.effective_config_hash = effective_hash
                            config_request.completed_at = datetime.utcnow()
                            logger.info(f"[OpAMP] ✓ Updated ConfigRequest {config_request.tracking_id} to completed for instance {instance_id} (config size: {len(effective_config_yaml) if effective_config_yaml else 0} bytes, hash: {effective_hash})")
                        
                        if pending_requests:
                            self.db.commit()
                            logger.info(f"[OpAMP] ✓ Committed {len(pending_requests)} ConfigRequest(s) as completed for instance {instance_id}")
                        else:
                            logger.warning(f"[OpAMP] No pending ConfigRequests found for {instance_id} even though effective_config was received")
                    except Exception as e:
                        logger.warning(f"Failed to update ConfigRequest records: {e}", exc_info=True)
                        self.db.rollback()
                        # Don't fail the whole operation if ConfigRequest update fails
        
        # Detect if this is a supervisor-managed agent
        # Supervisor typically sends agent_description and health fields
        is_supervisor_managed = message.HasField("agent_description") or message.HasField("health")
        
        # Extract agent description for version info (if present)
        if message.HasField("agent_description"):
            agent_desc = message.agent_description
            # Update gateway metadata with version info
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                # Update management mode if supervisor-managed
                if is_supervisor_managed:
                    gateway.management_mode = ManagementMode.SUPERVISOR.value
                
                metadata = gateway.extra_metadata or {}
                # AgentDescription doesn't have "version" or "name" fields directly
                # Version and name are in identifying_attributes as KeyValue pairs
                # Extract them from identifying_attributes instead
                # In proto3, repeated fields don't have presence - check if non-empty instead
                if agent_desc.identifying_attributes:
                    # Store identifying attributes
                    attrs = {}
                    for attr in agent_desc.identifying_attributes:
                        # In proto3, string fields don't have presence - check if non-empty
                        # value is a message field, so HasField() is correct
                        if attr.key and attr.HasField("value"):
                            # AnyValue uses oneof - check which variant is set
                            if attr.value.HasField("string_value"):
                                attrs[attr.key] = attr.value.string_value
                            else:
                                attrs[attr.key] = str(attr.value)
                    metadata["identifying_attributes"] = attrs
                gateway.extra_metadata = metadata
                self.gateway_service.repository.update(gateway)
        
        # Extract health information (if present)
        if message.HasField("health"):
            health = message.health
            # Update gateway metadata with health info
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                metadata = gateway.extra_metadata or {}
                health_info = metadata.get("health", {})
                
                # Log health details for debugging
                # In proto3, bool, fixed64, and string fields don't have presence
                # They're always present with default values (False, 0, "")
                healthy_value = health.healthy
                start_time = health.start_time_unix_nano if health.start_time_unix_nano != 0 else None
                last_error = health.last_error if health.last_error else None
                logger.info(f"[OpAMP] Health message from {instance_id}: healthy={healthy_value}, start_time={start_time}, last_error={last_error}")
                
                health_info["healthy"] = healthy_value
                logger.info(f"[OpAMP] Health status for {instance_id}: healthy={healthy_value}")
                
                if start_time:
                    health_info["start_time_unix_nano"] = start_time
                    logger.debug(f"[OpAMP] Health start_time for {instance_id}: {start_time}")
                
                if last_error:
                    health_info["last_error"] = last_error
                    logger.warning(f"[OpAMP] Health error for {instance_id}: {last_error}")
                
                metadata["health"] = health_info
                gateway.extra_metadata = metadata
                self.gateway_service.repository.update(gateway)
                logger.debug(f"[OpAMP] Updated health info for {instance_id}: {health_info}")
        
        # Store supervisor-specific status if supervisor-managed
        if is_supervisor_managed:
            supervisor_status = {}
            
            # Extract agent_description if present
            if message.HasField("agent_description"):
                agent_desc = message.agent_description
                
                # Log detailed agent description information
                identifying_attrs = []
                non_identifying_attrs = []
                
                if agent_desc.identifying_attributes:
                    for attr in agent_desc.identifying_attributes:
                        # In proto3, string fields don't have presence - check if non-empty
                        # value is a message field, so HasField() is correct
                        if attr.key and attr.HasField("value"):
                            # AnyValue uses oneof - check which variant is set
                            if attr.value.HasField("string_value"):
                                value_str = attr.value.string_value
                            else:
                                value_str = str(attr.value)
                            identifying_attrs.append({"key": attr.key, "value": value_str})
                            logger.info(f"[OpAMP] Agent {instance_id} identifying attribute: {attr.key} = {value_str}")
                
                if agent_desc.non_identifying_attributes:
                    for attr in agent_desc.non_identifying_attributes:
                        # In proto3, string fields don't have presence - check if non-empty
                        # value is a message field, so HasField() is correct
                        if attr.key and attr.HasField("value"):
                            # AnyValue uses oneof - check which variant is set
                            if attr.value.HasField("string_value"):
                                value_str = attr.value.string_value
                            else:
                                value_str = str(attr.value)
                            non_identifying_attrs.append({"key": attr.key, "value": value_str})
                            logger.info(f"[OpAMP] Agent {instance_id} non-identifying attribute: {attr.key} = {value_str}")
                
                logger.info(f"[OpAMP] Agent {instance_id} agent_description summary: {len(identifying_attrs)} identifying attributes, {len(non_identifying_attrs)} non-identifying attributes")
                
                supervisor_status["agent_description"] = {
                    "identifying_attributes": identifying_attrs,
                    "non_identifying_attributes": non_identifying_attrs,
                }
            else:
                logger.warning(f"[OpAMP] Agent {instance_id} did NOT send agent_description in this message")
            
            # Extract health if present
            if message.HasField("health"):
                health = message.health
                # In proto3, bool fields don't have presence - they're always present with default value (False)
                healthy_value = health.healthy
                
                # Log detailed health information
                logger.info(f"[OpAMP] Agent {instance_id} health details:")
                logger.info(f"  - healthy: {healthy_value}")
                # In proto3, fixed64 and string fields don't have presence - check if non-zero/non-empty
                start_time = health.start_time_unix_nano if health.start_time_unix_nano != 0 else None
                logger.info(f"  - start_time_unix_nano: {start_time if start_time else 'not set (0)'}")
                last_error = health.last_error if health.last_error else None
                logger.info(f"  - last_error: {last_error if last_error else 'not set (empty)'}")
                status_str = health.status if health.status else None
                logger.info(f"  - status: {status_str if status_str else 'not set (empty)'}")
                status_time = health.status_time_unix_nano if health.status_time_unix_nano != 0 else None
                logger.info(f"  - status_time_unix_nano: {status_time if status_time else 'not set (0)'}")
                
                # Log component health if present
                # In proto3, map fields don't have presence - check if non-empty instead
                # The field is component_health_map in proto, but Python may expose it as components
                component_map = getattr(health, 'component_health_map', None) or getattr(health, 'components', None)
                if component_map and len(component_map) > 0:
                    logger.info(f"  - components health: {len(component_map)} components reported")
                    for comp_name, comp_health in component_map.items():
                        # In proto3, bool and string fields don't have presence
                        comp_healthy = comp_health.healthy
                        comp_status = comp_health.status if comp_health.status else "not set"
                        logger.info(f"    - {comp_name}: healthy={comp_healthy}, status={comp_status}")
                
                supervisor_status["health"] = {
                    "healthy": healthy_value,
                    "start_time_unix_nano": start_time,
                    "last_error": last_error,
                    "status": status_str,
                    "status_time_unix_nano": status_time,
                }
            else:
                logger.warning(f"[OpAMP] Agent {instance_id} did NOT send health in this message")
            
            # Update supervisor status (merge with existing stored data to avoid overwriting other sections)
            if supervisor_status:
                existing_status = dict(gateway.supervisor_status or {})
                existing_status.update(supervisor_status)
                self.supervisor_service.update_supervisor_status(
                    instance_id,
                    existing_status
                )
        
        # Handle PackageStatuses message (if present)
        if message.HasField("package_statuses"):
            package_statuses = message.package_statuses
            logger.info(f"[OpAMP] Agent {instance_id} package_statuses received:")
            # In proto3, bytes and string fields don't have presence - check if non-empty instead
            hash_bytes = package_statuses.server_provided_all_packages_hash
            hash_str = bytes_to_hash_str(hash_bytes)
            logger.info(f"  - server_provided_all_packages_hash: {hash_str if hash_str else 'not set (empty)'}")
            error_msg = package_statuses.error_message if package_statuses.error_message else None
            logger.info(f"  - error_message: {error_msg if error_msg else 'not set (empty)'}")
            logger.info(f"  - packages count: {len(package_statuses.packages)}")
            
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                for package_name, package_status in package_statuses.packages.items():
                    # Log detailed package status
                    logger.info(f"  - Package '{package_name}':")
                    logger.info(f"    - status: {package_status.status}")
                    # In proto3, string and bytes fields don't have presence - check if non-empty instead
                    agent_version = package_status.agent_has_version if package_status.agent_has_version else None
                    logger.info(f"    - agent_has_version: {agent_version if agent_version else 'not set (empty)'}")
                    agent_hash_bytes = package_status.agent_has_hash
                    agent_hash_str = bytes_to_hash_str(agent_hash_bytes)
                    logger.info(f"    - agent_has_hash: {agent_hash_str if agent_hash_str else 'not set (empty)'}")
                    server_version = package_status.server_offered_version if package_status.server_offered_version else None
                    logger.info(f"    - server_offered_version: {server_version if server_version else 'not set (empty)'}")
                    server_hash_bytes = package_status.server_offered_hash
                    server_hash_str = bytes_to_hash_str(server_hash_bytes)
                    logger.info(f"    - server_offered_hash: {server_hash_str if server_hash_str else 'not set (empty)'}")
                    pkg_error_msg = package_status.error_message if package_status.error_message else None
                    logger.info(f"    - error_message: {pkg_error_msg if pkg_error_msg else 'not set (empty)'}")
                    
                    # Map OpAMP package status to our model
                    status_mapping = {
                        opamp_pb2.PackageStatusEnum.PackageStatusEnum_Installed: PackageStatus.INSTALLED,
                        opamp_pb2.PackageStatusEnum.PackageStatusEnum_Installing: PackageStatus.INSTALLING,
                        opamp_pb2.PackageStatusEnum.PackageStatusEnum_InstallFailed: PackageStatus.FAILED,
                        opamp_pb2.PackageStatusEnum.PackageStatusEnum_NotInstalled: PackageStatus.UNINSTALLED,
                    }
                    opamp_status = status_mapping.get(
                        package_status.status,
                        PackageStatus.UNINSTALLED
                    )
                    
                    # In proto3, bytes and string fields don't have presence - check if non-empty instead
                    agent_hash = None
                    hash_bytes = package_status.agent_has_hash
                    if hash_bytes and len(hash_bytes) > 0:
                        try:
                            agent_hash = bytes_to_hash_str(hash_bytes)
                        except (ValueError, AttributeError):
                            pass
                    
                    error_msg = package_status.error_message if package_status.error_message else None
                    
                    self.package_service.update_package_status(
                        gateway_id=gateway.id,
                        package_name=package_name,
                        status=opamp_status,
                        agent_reported_hash=agent_hash,
                        error_message=error_msg
                    )
        else:
            logger.warning(f"[OpAMP] Agent {instance_id} did NOT send package_statuses in this message")
        
        # Handle ConnectionSettingsRequest message (if present)
        if message.HasField("connection_settings_request"):
            connection_request = message.connection_settings_request
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                # Handle CSR (Certificate Signing Request) if present
                if connection_request.HasField("opamp"):
                    opamp_request = connection_request.opamp
                    if opamp_request.HasField("certificate_signing_request"):
                        csr_pem = opamp_request.certificate_signing_request
                        # Handle CSR and generate certificate
                        self.connection_settings_service.handle_csr_request(
                            gateway_id=gateway.id,
                            org_id=gateway.org_id,
                            csr_pem=csr_pem
                        )
        
        # Handle ConnectionSettingsStatus message (if present)
        if message.HasField("connection_settings_status"):
            connection_status = message.connection_settings_status
            logger.info(f"[OpAMP] Agent {instance_id} connection_settings_status received:")
            # ConnectionSettingsStatus only has: last_connection_settings_hash (bytes), status (enum), error_message (string)
            # In proto3, bytes, enum, and string fields don't have presence
            hash_bytes = connection_status.last_connection_settings_hash
            hash_str = bytes_to_hash_str(hash_bytes)
            logger.info(f"  - last_connection_settings_hash: {hash_str if hash_str else 'not set (empty)'}")
            logger.info(f"  - status: {connection_status.status}")
            error_msg = connection_status.error_message if connection_status.error_message else None
            logger.info(f"  - error_message: {error_msg if error_msg else 'not set (empty)'}")
            
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                # Map OpAMP connection settings status to our model
                status_mapping = {
                    opamp_pb2.ConnectionSettingsStatus.ConnectionSettingsStatus_UNSET: ConnectionSettingsStatus.UNSET,
                    opamp_pb2.ConnectionSettingsStatus.ConnectionSettingsStatus_APPLIED: ConnectionSettingsStatus.APPLIED,
                    opamp_pb2.ConnectionSettingsStatus.ConnectionSettingsStatus_APPLYING: ConnectionSettingsStatus.APPLYING,
                    opamp_pb2.ConnectionSettingsStatus.ConnectionSettingsStatus_FAILED: ConnectionSettingsStatus.FAILED,
                }
                
                opamp_status = status_mapping.get(
                    connection_status.status,
                    ConnectionSettingsStatus.UNSET
                )
                
                settings_hash = None
                # ConnectionSettingsStatus uses last_connection_settings_hash to identify which settings were applied
                hash_bytes = connection_status.last_connection_settings_hash
                if hash_bytes and len(hash_bytes) > 0:
                    try:
                        settings_hash = bytes_to_hash_str(hash_bytes)
                    except (ValueError, AttributeError):
                        pass
                
                # In proto3, string fields don't have presence - check if non-empty instead
                error_msg = connection_status.error_message if connection_status.error_message else None
                
                if settings_hash:
                    self.connection_settings_service.update_connection_setting_status(
                        gateway_id=gateway.id,
                        settings_hash=settings_hash,
                        status=opamp_status,
                        error_message=error_msg
                    )
        
        # Handle AvailableComponents message (if present)
        if message.HasField("available_components"):
            available_components = message.available_components
            logger.info(f"[OpAMP] Agent {instance_id} available_components received:")
            
            # In proto3, bytes fields don't have presence - check if non-empty
            hash_bytes = available_components.hash
            hash_str = bytes_to_hash_str(hash_bytes)
            logger.info(f"  - hash: {hash_str if hash_str else 'not set (empty)'}")
            logger.info(f"  - components count: {len(available_components.components)}")
            
            # Parse all components
            parsed_components = []
            for component_id, component_details in available_components.components.items():
                logger.info(f"  - Parsing component: {component_id}")
                parsed_component = parse_component_details(component_details, component_id)
                parsed_components.append(parsed_component)
                logger.info(f"    - Type: {parsed_component['component_type']}, Sub-components: {len(parsed_component.get('sub_components', []))}")
            
            # Store in supervisor_status
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                supervisor_status_data = {
                    "components": parsed_components,
                    "hash": hash_str,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Update supervisor_status with available_components
                current_supervisor_status = dict(gateway.supervisor_status or {})
                current_supervisor_status["available_components"] = supervisor_status_data
                
                self.supervisor_service.update_supervisor_status(
                    instance_id,
                    current_supervisor_status
                )
                logger.info(f"[OpAMP] Stored {len(parsed_components)} available components for {instance_id}")
        else:
            logger.warning(f"[OpAMP] Agent {instance_id} did NOT send available_components in this message")
        
        # Handle agent telemetry data (own_metrics) if present
        # Note: AgentToServer message does NOT have a "metrics" field in the OpAMP protocol
        # Metrics are sent separately via telemetry (traces, metrics, logs) endpoints, not in OpAMP messages
        # The REPORTS_OWN_METRICS capability indicates the agent can send metrics via telemetry endpoints,
        # but metrics are not included in the AgentToServer protobuf message itself
        # Removed incorrect metrics field access that was causing "Protocol message AgentToServer has no 'metrics' field" errors
        
        # Build ServerToAgent Protobuf message
        server_message = opamp_pb2.ServerToAgent()
        
        # Set instance UID (must be 16 bytes per OpAMP spec - UUID v7 format)
        try:
            gateway_uuid = UUID(str(gateway.id))
            # UUID.bytes gives us 16 bytes
            server_message.instance_uid = gateway_uuid.bytes
        except (ValueError, AttributeError):
            # Fallback: convert string to 16 bytes
            gateway_id_str = str(gateway.id)
            # Pad or truncate to 16 bytes
            server_message.instance_uid = gateway_id_str.encode('utf-8')[:16].ljust(16, b'\x00')
        
        # Set server capabilities
        server_message.capabilities = server_capabilities
        
        # Request effective config if agent supports it and we don't have it OR if there's a pending ConfigRequest
        # Use ReportFullState flag to request agent to report full state including effective_config
        if gateway.opamp_agent_capabilities and (gateway.opamp_agent_capabilities & AgentCapabilities.REPORTS_EFFECTIVE_CONFIG):
            # Check if we don't have effective config content OR if there's a pending ConfigRequest
            from app.models.config_request import ConfigRequest, ConfigRequestStatus
            pending_requests = self.db.query(ConfigRequest).filter(
                ConfigRequest.instance_id == instance_id,
                ConfigRequest.status == ConfigRequestStatus.PENDING
            ).all()
            
            logger.info(f"[OpAMP] Checking if ReportFullState needed for {instance_id}: has_effective_config_content={bool(gateway.opamp_effective_config_content)}, pending_requests_count={len(pending_requests)}")
            
            if not gateway.opamp_effective_config_content or pending_requests:
                # Set ReportFullState flag to request agent to report full state
                # This will cause agent to include effective_config in next message
                # Use OR operation to preserve any existing flags
                old_flags = server_message.flags
                server_message.flags = server_message.flags | opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
                if pending_requests:
                    logger.info(f"[OpAMP] ✓ Setting ReportFullState flag for agent {instance_id} due to {len(pending_requests)} pending ConfigRequest(s): {[r.tracking_id for r in pending_requests]}")
                else:
                    logger.info(f"[OpAMP] ✓ Setting ReportFullState flag for agent {instance_id} (no effective config content stored)")
                logger.info(f"[OpAMP] ServerToAgent flags: 0x{old_flags:X} -> 0x{server_message.flags:X} (ReportFullState={bool(server_message.flags & opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState)})")
            else:
                logger.info(f"[OpAMP] Not setting ReportFullState for {instance_id} (has config content and no pending requests)")
        
        # Request AvailableComponents if agent supports it and we don't have the data
        # Also check if there's a manual request flag in metadata
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        should_request = False
        
        if gateway:
            # Check for manual request flag in metadata
            metadata = gateway.extra_metadata or {}
            if metadata.get("request_available_components"):
                should_request = True
                # Clear the flag
                metadata.pop("request_available_components", None)
                gateway.extra_metadata = metadata
                self.gateway_service.repository.update(gateway)
                logger.info(f"[OpAMP] Manual request for AvailableComponents detected for {instance_id}")
        
        if AgentCapabilities.REPORTS_AVAILABLE_COMPONENTS in agent_caps:
            if gateway:
                supervisor_status = gateway.supervisor_status or {}
                available_components = supervisor_status.get("available_components")
                
                if should_request or (not available_components or not available_components.get("components")):
                    # Request available components
                    old_flags = server_message.flags
                    server_message.flags = server_message.flags | opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportAvailableComponents
                    reason = "manual request" if should_request else "no available components data"
                    logger.info(f"[OpAMP] Setting ReportAvailableComponents flag for {instance_id} ({reason})")
                    logger.info(f"[OpAMP] ServerToAgent flags: 0x{old_flags:X} -> 0x{server_message.flags:X} (ReportAvailableComponents={bool(server_message.flags & opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportAvailableComponents)})")
                else:
                    logger.debug(f"[OpAMP] Not setting ReportAvailableComponents for {instance_id} (already have {len(available_components.get('components', []))} components)")
        
        # Handle remote config status if agent reports it (already processed above, but also update config version)
        if message.HasField("remote_config_status"):
            remote_config_status = message.remote_config_status
            logger.info(f"[OpAMP] Agent {instance_id} remote_config_status (config version handler):")
            logger.info(f"  - status: {remote_config_status.status}")
            # In proto3, bytes fields don't have presence - check if non-empty instead
            hash_bytes = remote_config_status.last_remote_config_hash
            hash_str = bytes_to_hash_str(hash_bytes)
            logger.info(f"  - last_remote_config_hash: {hash_str if hash_str else 'not set (empty)'}")
            # Agent is reporting status of last config we sent
            # Update gateway's config version if needed
            if remote_config_status.status == opamp_pb2.RemoteConfigStatuses.RemoteConfigStatuses_APPLIED:
                config_hash = remote_config_status.last_remote_config_hash
                # Try to extract version from hash if it's a string
                try:
                    hash_str = bytes_to_hash_str(config_hash)
                    if hash_str and hash_str.startswith("v"):
                        version = int(hash_str[1:])
                        self.opamp_service.update_gateway_config_version(instance_id, version)
                except (ValueError, AttributeError):
                    pass
        
        # Check if agent accepts remote config before sending any
        # AgentCapabilities is already imported at the top of the file
        accepts_remote_config = AgentCapabilities.ACCEPTS_REMOTE_CONFIG in agent_caps
        
        # Only send remote config if agent accepts it
        if accepts_remote_config:
            # Check if we need to send new config
            # First check for pending OpAMP config deployments
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                from app.models.opamp_config_deployment import OpAMPConfigDeployment, OpAMPConfigDeploymentStatus
                from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
                
                # Check for pending deployment for this gateway
                pending_audit = self.db.query(OpAMPConfigAudit).join(OpAMPConfigDeployment).filter(
                    and_(
                        OpAMPConfigAudit.gateway_id == gateway.id,
                        OpAMPConfigAudit.status == OpAMPConfigAuditStatus.PENDING,
                        OpAMPConfigDeployment.status.in_([
                            OpAMPConfigDeploymentStatus.PENDING,
                            OpAMPConfigDeploymentStatus.IN_PROGRESS
                        ])
                    )
                ).order_by(OpAMPConfigAudit.created_at.desc()).first()
                
                if pending_audit:
                    # Send config from pending deployment
                    deployment = self.db.query(OpAMPConfigDeployment).filter(
                        OpAMPConfigDeployment.id == pending_audit.deployment_id
                    ).first()
                    
                    if deployment:
                        remote_config = opamp_pb2.AgentRemoteConfig()
                        
                        # Create config map
                        config_map = opamp_pb2.AgentConfigMap()
                        config_file = opamp_pb2.AgentConfigFile()
                        config_file.body = deployment.config_yaml.encode('utf-8')
                        config_file.content_type = "text/yaml"
                        config_map.config_map[""].CopyFrom(config_file)
                        
                        remote_config.config.CopyFrom(config_map)
                        remote_config.config_hash = deployment.config_hash.encode('utf-8')
                        
                        server_message.remote_config.CopyFrom(remote_config)
                        
                        # Update audit entry status to APPLYING
                        pending_audit.status = OpAMPConfigAuditStatus.APPLYING
                        pending_audit.updated_at = datetime.utcnow()
                        self.db.commit()
                        
                        return server_message
            
            # Fallback to legacy config from deployments/templates
            current_config = self.opamp_service.get_config_for_gateway(instance_id)
            if current_config:
                # Check if agent needs this config
                agent_config_hash = None
                if message.HasField("effective_config"):
                    # Agent has effective config, but we need to check if it matches
                    pass
                
                config_version = current_config.get("version", 0)
                config_yaml = current_config.get("config_yaml", "")
                
                # Always send config for now (can be optimized later)
                remote_config = opamp_pb2.AgentRemoteConfig()
                
                # Create config map
                config_map = opamp_pb2.AgentConfigMap()
                config_file = opamp_pb2.AgentConfigFile()
                config_file.body = config_yaml.encode('utf-8')
                config_file.content_type = "text/yaml"
                # Use empty string as key for main config
                config_map.config_map[""].CopyFrom(config_file)
                
                remote_config.config.CopyFrom(config_map)
                remote_config.config_hash = f"v{config_version}".encode('utf-8')
                
                server_message.remote_config.CopyFrom(remote_config)
                
                # Store remote config hash
                self.gateway_service.update_opamp_config_hashes(
                    instance_id,
                    effective_config_hash=None,  # Don't overwrite
                    remote_config_hash=f"v{config_version}"
                )
        
        # Handle PackagesAvailable - send packages if agent accepts them
        accepts_packages = AgentCapabilities.ACCEPTS_PACKAGES in agent_caps
        
        if accepts_packages:
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                packages_available = self.package_service.get_packages_available_for_gateway(
                    gateway.id, gateway.org_id
                )
                
                if packages_available:
                    packages_msg = opamp_pb2.PackagesAvailable()
                    
                    # Calculate aggregate hash of all packages
                    import hashlib
                    all_packages_data = []
                    for pkg in packages_available:
                        pkg_data = f"{pkg['package_name']}:{pkg.get('package_hash', '')}"
                        all_packages_data.append(pkg_data)
                    
                    all_packages_hash = hashlib.sha256(
                        ":".join(sorted(all_packages_data)).encode()
                    ).digest()
                    packages_msg.all_packages_hash = all_packages_hash
                    
                    # Add each package
                    for pkg in packages_available:
                        package_available = opamp_pb2.PackageAvailable()
                        
                        # Create downloadable file
                        downloadable_file = opamp_pb2.DownloadableFile()
                        downloadable_file.download_url = pkg.get('download_url', '')
                        if pkg.get('content_hash'):
                            downloadable_file.content_hash = pkg['content_hash'].encode('utf-8')
                        if pkg.get('signature'):
                            # Signature is already bytes from hex string
                            downloadable_file.signature = bytes.fromhex(pkg['signature']) if isinstance(pkg['signature'], str) else pkg['signature']
                        
                        package_available.file.CopyFrom(downloadable_file)
                        package_available.hash = pkg.get('package_hash', '').encode('utf-8')
                        
                        # Set package type
                        if pkg.get('package_type') == 'addon':
                            package_available.type = opamp_pb2.PackageType.PackageType_Addon
                        else:
                            package_available.type = opamp_pb2.PackageType.PackageType_TopLevel
                        
                        packages_msg.packages[pkg['package_name']] = package_available
                    
                    server_message.packages_available.CopyFrom(packages_msg)
        
        # Handle ConnectionSettingsOffers - send connection settings if agent accepts them
        accepts_opamp_connection = AgentCapabilities.ACCEPTS_OPAMP_CONNECTION_SETTINGS in agent_caps
        accepts_other_connection = AgentCapabilities.ACCEPTS_OTHER_CONNECTION_SETTINGS in agent_caps
        
        if accepts_opamp_connection or accepts_other_connection:
            gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
            if gateway:
                connection_settings_offers = self.connection_settings_service.get_connection_settings_offers_for_gateway(
                    gateway.id, gateway.org_id
                )
                
                if connection_settings_offers:
                    offers_msg = opamp_pb2.ConnectionSettingsOffers()
                    
                    # OpAMP connection settings
                    if connection_settings_offers.get('opamp'):
                        opamp_settings = opamp_pb2.OpAMPConnectionSettings()
                        opamp_data = connection_settings_offers['opamp']
                        
                        if 'endpoint' in opamp_data:
                            opamp_settings.destination.endpoint = opamp_data['endpoint']
                        if 'headers' in opamp_data:
                            for key, value in opamp_data['headers'].items():
                                opamp_settings.destination.headers[key] = value
                        if 'tls' in opamp_data:
                            tls = opamp_data['tls']
                            if 'cert' in tls:
                                opamp_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                            if 'key' in tls:
                                opamp_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                            if 'ca_cert' in tls:
                                opamp_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                        
                        offers_msg.opamp.CopyFrom(opamp_settings)
                    
                    # Own metrics destination
                    if connection_settings_offers.get('own_metrics'):
                        metrics_settings = opamp_pb2.TelemetryConnectionSettings()
                        metrics_data = connection_settings_offers['own_metrics']
                        
                        if 'endpoint' in metrics_data:
                            metrics_settings.destination.endpoint = metrics_data['endpoint']
                        if 'headers' in metrics_data:
                            for key, value in metrics_data['headers'].items():
                                metrics_settings.destination.headers[key] = value
                        if 'tls' in metrics_data:
                            tls = metrics_data['tls']
                            if 'cert' in tls:
                                metrics_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                            if 'key' in tls:
                                metrics_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                            if 'ca_cert' in tls:
                                metrics_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                        
                        offers_msg.own_metrics.CopyFrom(metrics_settings)
                    
                    # Own traces destination
                    if connection_settings_offers.get('own_traces'):
                        traces_settings = opamp_pb2.TelemetryConnectionSettings()
                        traces_data = connection_settings_offers['own_traces']
                        
                        if 'endpoint' in traces_data:
                            traces_settings.destination.endpoint = traces_data['endpoint']
                        if 'headers' in traces_data:
                            for key, value in traces_data['headers'].items():
                                traces_settings.destination.headers[key] = value
                        if 'tls' in traces_data:
                            tls = traces_data['tls']
                            if 'cert' in tls:
                                traces_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                            if 'key' in tls:
                                traces_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                            if 'ca_cert' in tls:
                                traces_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                        
                        offers_msg.own_traces.CopyFrom(traces_settings)
                    
                    # Own logs destination
                    if connection_settings_offers.get('own_logs'):
                        logs_settings = opamp_pb2.TelemetryConnectionSettings()
                        logs_data = connection_settings_offers['own_logs']
                        
                        if 'endpoint' in logs_data:
                            logs_settings.destination.endpoint = logs_data['endpoint']
                        if 'headers' in logs_data:
                            for key, value in logs_data['headers'].items():
                                logs_settings.destination.headers[key] = value
                        if 'tls' in logs_data:
                            tls = logs_data['tls']
                            if 'cert' in tls:
                                logs_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                            if 'key' in tls:
                                logs_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                            if 'ca_cert' in tls:
                                logs_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                        
                        offers_msg.own_logs.CopyFrom(logs_settings)
                    
                    # Other connection settings
                    if connection_settings_offers.get('other_connections'):
                        for name, other_data in connection_settings_offers['other_connections'].items():
                            other_settings = opamp_pb2.OtherConnectionSettings()
                            
                            if 'endpoint' in other_data:
                                other_settings.destination.endpoint = other_data['endpoint']
                            if 'headers' in other_data:
                                for key, value in other_data['headers'].items():
                                    other_settings.destination.headers[key] = value
                            if 'tls' in other_data:
                                tls = other_data['tls']
                                if 'cert' in tls:
                                    other_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                                if 'key' in tls:
                                    other_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                                if 'ca_cert' in tls:
                                    other_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                            
                            offers_msg.other_connections[name] = other_settings
                    
                    server_message.connection_settings.CopyFrom(offers_msg)
        
        # Summary log of what was received from agent
        logger.info(f"[OpAMP] ===== Agent {instance_id} message processing summary =====")
        logger.info(f"  - Sequence number: {message.sequence_num}")
        logger.info(f"  - Capabilities: 0x{message.capabilities:X} ({message.capabilities})")
        logger.info(f"  - Has agent_description: {message.HasField('agent_description')}")
        logger.info(f"  - Has health: {message.HasField('health')}")
        logger.info(f"  - Has effective_config: {message.HasField('effective_config')}")
        logger.info(f"  - Has remote_config_status: {message.HasField('remote_config_status')}")
        logger.info(f"  - Has package_statuses: {message.HasField('package_statuses')}")
        logger.info(f"  - Has connection_settings_status: {message.HasField('connection_settings_status')}")
        logger.info(f"  - Has available_components: {message.HasField('available_components')}")
        if message.HasField('available_components'):
            logger.info(f"  - Available components count: {len(message.available_components.components)}")
        logger.info(f"[OpAMP] ===== End of message processing summary =====")
        
        return server_message
    
    def build_initial_server_message(
        self,
        instance_id: str
    ) -> opamp_pb2.ServerToAgent:
        """
        Build initial ServerToAgent message for agent connection
        
        Args:
            instance_id: Gateway instance identifier
        
        Returns:
            ServerToAgent Protobuf message
        """
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if not gateway:
            raise ValueError(f"Gateway not found: {instance_id}")
        
        server_capabilities = ServerCapabilities.get_all_capabilities()
        
        # Create ServerToAgent Protobuf message
        message = opamp_pb2.ServerToAgent()
        
        # Set instance UID (must be 16 bytes per OpAMP spec - UUID v7 format)
        try:
            gateway_uuid = UUID(str(gateway.id))
            # UUID.bytes gives us 16 bytes
            message.instance_uid = gateway_uuid.bytes
        except (ValueError, AttributeError):
            # Fallback: convert string to 16 bytes
            gateway_id_str = str(gateway.id)
            # Pad or truncate to 16 bytes
            message.instance_uid = gateway_id_str.encode('utf-8')[:16].ljust(16, b'\x00')
        
        # Set server capabilities
        message.capabilities = server_capabilities
        
        # Request effective config on initial connection if agent supports it OR if there's a pending ConfigRequest
        # Use ReportFullState flag to request agent to report full state including effective_config
        agent_capabilities = gateway.opamp_agent_capabilities or 0
        if agent_capabilities & AgentCapabilities.REPORTS_EFFECTIVE_CONFIG:
            # Check if there's a pending ConfigRequest
            from app.models.config_request import ConfigRequest, ConfigRequestStatus
            pending_requests = self.db.query(ConfigRequest).filter(
                ConfigRequest.instance_id == instance_id,
                ConfigRequest.status == ConfigRequestStatus.PENDING
            ).all()
            
            # Request full state including effective_config if we don't have it or there's a pending request
            if not gateway.opamp_effective_config_content or pending_requests:
                message.flags = message.flags | opamp_pb2.ServerToAgentFlags.ServerToAgentFlags_ReportFullState
                if pending_requests:
                    logger.debug(f"Requesting effective config from agent {instance_id} on initial connection due to pending ConfigRequest(s)")
                else:
                    logger.debug(f"Requesting effective config from agent {instance_id} on initial connection")
        
        # Include initial config if available
        # First check for pending OpAMP config deployments
        gateway = self.gateway_service.repository.get_by_instance_id(instance_id)
        if gateway:
            from app.models.opamp_config_deployment import OpAMPConfigDeployment, OpAMPConfigDeploymentStatus
            from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
            
            # Check for pending deployment for this gateway
            pending_audit = self.db.query(OpAMPConfigAudit).join(OpAMPConfigDeployment).filter(
                and_(
                    OpAMPConfigAudit.gateway_id == gateway.id,
                    OpAMPConfigAudit.status == OpAMPConfigAuditStatus.PENDING,
                    OpAMPConfigDeployment.status.in_([
                        OpAMPConfigDeploymentStatus.PENDING,
                        OpAMPConfigDeploymentStatus.IN_PROGRESS
                    ])
                )
            ).order_by(OpAMPConfigAudit.created_at.desc()).first()
            
            if pending_audit:
                # Send config from pending deployment
                deployment = self.db.query(OpAMPConfigDeployment).filter(
                    OpAMPConfigDeployment.id == pending_audit.deployment_id
                ).first()
                
                if deployment:
                    remote_config = opamp_pb2.AgentRemoteConfig()
                    
                    # Create config map
                    config_map = opamp_pb2.AgentConfigMap()
                    config_file = opamp_pb2.AgentConfigFile()
                    config_file.body = deployment.config_yaml.encode('utf-8')
                    config_file.content_type = "text/yaml"
                    config_map.config_map[""].CopyFrom(config_file)
                    
                    remote_config.config.CopyFrom(config_map)
                    remote_config.config_hash = deployment.config_hash.encode('utf-8')
                    
                    message.remote_config.CopyFrom(remote_config)
                    
                    # Update audit entry status to APPLYING
                    pending_audit.status = OpAMPConfigAuditStatus.APPLYING
                    pending_audit.updated_at = datetime.utcnow()
                    self.db.commit()
                    
                    return message
        
        # Fallback to legacy config from deployments/templates
        config = self.opamp_service.get_config_for_gateway(instance_id)
        if config:
            remote_config = opamp_pb2.AgentRemoteConfig()
            
            # Create config map
            config_map = opamp_pb2.AgentConfigMap()
            config_file = opamp_pb2.AgentConfigFile()
            config_file.body = config.get("config_yaml", "").encode('utf-8')
            config_file.content_type = "text/yaml"
            # Use empty string as key for main config
            config_map.config_map[""].CopyFrom(config_file)
            
            remote_config.config.CopyFrom(config_map)
            config_version = config.get('version', 0)
            remote_config.config_hash = f"v{config_version}".encode('utf-8')
            
            message.remote_config.CopyFrom(remote_config)
            
            # Store remote config hash
            self.gateway_service.update_opamp_config_hashes(
                instance_id,
                effective_config_hash=None,  # Don't overwrite
                remote_config_hash=f"v{config_version}"
            )
        
        # Add packages and connection settings to initial message
        # Note: We assume agent accepts these capabilities for initial message
        # In practice, we should check agent capabilities from first message
        
        # Add packages if available
        packages_available = self.package_service.get_packages_available_for_gateway(
            gateway.id, gateway.org_id
        )
        
        if packages_available:
            packages_msg = opamp_pb2.PackagesAvailable()
            
            # Calculate aggregate hash of all packages
            import hashlib
            all_packages_data = []
            for pkg in packages_available:
                pkg_data = f"{pkg['package_name']}:{pkg.get('package_hash', '')}"
                all_packages_data.append(pkg_data)
            
            all_packages_hash = hashlib.sha256(
                ":".join(sorted(all_packages_data)).encode()
            ).digest()
            packages_msg.all_packages_hash = all_packages_hash
            
            # Add each package
            for pkg in packages_available:
                package_available = opamp_pb2.PackageAvailable()
                
                # Create downloadable file
                downloadable_file = opamp_pb2.DownloadableFile()
                downloadable_file.download_url = pkg.get('download_url', '')
                if pkg.get('content_hash'):
                    downloadable_file.content_hash = pkg['content_hash'].encode('utf-8')
                if pkg.get('signature'):
                    downloadable_file.signature = bytes.fromhex(pkg['signature']) if isinstance(pkg['signature'], str) else pkg['signature']
                
                package_available.file.CopyFrom(downloadable_file)
                package_available.hash = pkg.get('package_hash', '').encode('utf-8')
                
                # Set package type
                if pkg.get('package_type') == 'addon':
                    package_available.type = opamp_pb2.PackageType.PackageType_Addon
                else:
                    package_available.type = opamp_pb2.PackageType.PackageType_TopLevel
                
                packages_msg.packages[pkg['package_name']] = package_available
            
            message.packages_available.CopyFrom(packages_msg)
        
        # Add connection settings if available
        connection_settings_offers = self.connection_settings_service.get_connection_settings_offers_for_gateway(
            gateway.id, gateway.org_id
        )
        
        if connection_settings_offers:
            offers_msg = opamp_pb2.ConnectionSettingsOffers()
            
            # OpAMP connection settings
            if connection_settings_offers.get('opamp'):
                opamp_settings = opamp_pb2.OpAMPConnectionSettings()
                opamp_data = connection_settings_offers['opamp']
                
                if 'endpoint' in opamp_data:
                    opamp_settings.destination.endpoint = opamp_data['endpoint']
                if 'headers' in opamp_data:
                    for key, value in opamp_data['headers'].items():
                        opamp_settings.destination.headers[key] = value
                if 'tls' in opamp_data:
                    tls = opamp_data['tls']
                    if 'cert' in tls:
                        opamp_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                    if 'key' in tls:
                        opamp_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                    if 'ca_cert' in tls:
                        opamp_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                
                offers_msg.opamp.CopyFrom(opamp_settings)
            
            # Own metrics destination
            if connection_settings_offers.get('own_metrics'):
                metrics_settings = opamp_pb2.TelemetryConnectionSettings()
                metrics_data = connection_settings_offers['own_metrics']
                
                if 'endpoint' in metrics_data:
                    metrics_settings.destination.endpoint = metrics_data['endpoint']
                if 'headers' in metrics_data:
                    for key, value in metrics_data['headers'].items():
                        metrics_settings.destination.headers[key] = value
                if 'tls' in metrics_data:
                    tls = metrics_data['tls']
                    if 'cert' in tls:
                        metrics_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                    if 'key' in tls:
                        metrics_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                    if 'ca_cert' in tls:
                        metrics_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                
                offers_msg.own_metrics.CopyFrom(metrics_settings)
            
            # Own traces destination
            if connection_settings_offers.get('own_traces'):
                traces_settings = opamp_pb2.TelemetryConnectionSettings()
                traces_data = connection_settings_offers['own_traces']
                
                if 'endpoint' in traces_data:
                    traces_settings.destination.endpoint = traces_data['endpoint']
                if 'headers' in traces_data:
                    for key, value in traces_data['headers'].items():
                        traces_settings.destination.headers[key] = value
                if 'tls' in traces_data:
                    tls = traces_data['tls']
                    if 'cert' in tls:
                        traces_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                    if 'key' in tls:
                        traces_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                    if 'ca_cert' in tls:
                        traces_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                
                offers_msg.own_traces.CopyFrom(traces_settings)
            
            # Own logs destination
            if connection_settings_offers.get('own_logs'):
                logs_settings = opamp_pb2.TelemetryConnectionSettings()
                logs_data = connection_settings_offers['own_logs']
                
                if 'endpoint' in logs_data:
                    logs_settings.destination.endpoint = logs_data['endpoint']
                if 'headers' in logs_data:
                    for key, value in logs_data['headers'].items():
                        logs_settings.destination.headers[key] = value
                if 'tls' in logs_data:
                    tls = logs_data['tls']
                    if 'cert' in tls:
                        logs_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                    if 'key' in tls:
                        logs_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                    if 'ca_cert' in tls:
                        logs_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                
                offers_msg.own_logs.CopyFrom(logs_settings)
            
            # Other connection settings
            if connection_settings_offers.get('other_connections'):
                for name, other_data in connection_settings_offers['other_connections'].items():
                    other_settings = opamp_pb2.OtherConnectionSettings()
                    
                    if 'endpoint' in other_data:
                        other_settings.destination.endpoint = other_data['endpoint']
                    if 'headers' in other_data:
                        for key, value in other_data['headers'].items():
                            other_settings.destination.headers[key] = value
                    if 'tls' in other_data:
                        tls = other_data['tls']
                        if 'cert' in tls:
                            other_settings.destination.tls.certificate = tls['cert'] if isinstance(tls['cert'], bytes) else tls['cert'].encode()
                        if 'key' in tls:
                            other_settings.destination.tls.key = tls['key'] if isinstance(tls['key'], bytes) else tls['key'].encode()
                        if 'ca_cert' in tls:
                            other_settings.destination.tls.ca_certificate = tls['ca_cert'] if isinstance(tls['ca_cert'], bytes) else tls['ca_cert'].encode()
                    
                    offers_msg.other_connections[name] = other_settings
            
            message.connection_settings.CopyFrom(offers_msg)
        
        return message
    
    def parse_agent_message(self, data: bytes) -> opamp_pb2.AgentToServer:
        """
        Parse AgentToServer message from protobuf bytes
        
        Args:
            data: Raw message data (protobuf bytes)
        
        Returns:
            Parsed AgentToServer Protobuf message
        """
        if not data:
            return opamp_pb2.AgentToServer()
        
        # Try Go parser first (100% compatible with Go-based supervisor/collector)
        go_parser = get_go_parser()
        if go_parser:
            try:
                parsed_dict = go_parser.parse_agent_message(data)
                if parsed_dict:
                    # Log what Go parser extracted (especially capabilities)
                    capabilities_from_go = parsed_dict.get("capabilities", 0)
                    logger.info(
                        f"[OpAMP] Go parser extracted capabilities: 0x{capabilities_from_go:X} ({capabilities_from_go}) "
                        f"from raw message ({len(data)} bytes)"
                    )
                    
                    # Convert dict to protobuf message
                    agent_message = opamp_pb2.AgentToServer()
                    self._dict_to_agent_message(parsed_dict, agent_message)
                    
                    # Verify capabilities were set correctly
                    logger.info(
                        f"[OpAMP] After conversion to protobuf, capabilities: 0x{agent_message.capabilities:X} ({agent_message.capabilities})"
                    )
                    
                    logger.debug(f"Successfully parsed AgentToServer message using Go parser ({len(data)} bytes)")
                    return agent_message
            except Exception as e:
                logger.warning(f"Go parser failed, falling back to Python parser: {e}")
        
        # Fallback to Python parser
        try:
            agent_message = opamp_pb2.AgentToServer()
            agent_message.ParseFromString(data)
            logger.info(
                f"[OpAMP] Python parser extracted capabilities: 0x{agent_message.capabilities:X} ({agent_message.capabilities}) "
                f"from raw message ({len(data)} bytes)"
            )
            return agent_message
        except Exception as e:
            # If parsing fails, try MergeFromString as a fallback (more lenient, handles unknown fields)
            # This provides forward compatibility with newer protobuf versions or unknown fields
            try:
                agent_message = opamp_pb2.AgentToServer()
                agent_message.MergeFromString(data)
                logger.warning(
                    f"AgentToServer message failed ParseFromString but succeeded with MergeFromString "
                    f"(message size: {len(data)} bytes). This may indicate unknown fields in the message."
                )
                return agent_message
            except Exception as merge_error:
                # Both parsing methods failed - try to extract at least instance_uid and capabilities
                # from the raw protobuf wire format before giving up
                try:
                    # Try to manually parse key fields from the wire format
                    # Field 1 (instance_uid): bytes, field tag 0x0A (1 << 3 | 2)
                    # Field 4 (capabilities): uint64, field tag 0x20 (4 << 3 | 0)
                    agent_message = opamp_pb2.AgentToServer()
                    
                    # Try to extract instance_uid manually from protobuf wire format
                    # Protobuf wire format: tag (field_number << 3 | wire_type), then value
                    # For field 1 (instance_uid): tag = 0x0A (1 << 3 | 2), then length-prefixed bytes
                    pos = 0
                    instance_uid_found = False
                    while pos < len(data) and pos < 200:  # Check first 200 bytes for key fields
                        if pos >= len(data):
                            break
                        tag = data[pos]
                        pos += 1
                        
                        # Check if this is field 1 (instance_uid)
                        if tag == 0x0A:  # Field 1, wire type 2 (length-delimited)
                            if pos < len(data):
                                # Read varint length (can be multi-byte)
                                length = 0
                                shift = 0
                                while pos < len(data):
                                    byte = data[pos]
                                    pos += 1
                                    length |= (byte & 0x7F) << shift
                                    if not (byte & 0x80):
                                        break
                                    shift += 7
                                    if shift >= 32:  # Sanity check
                                        raise ValueError("Invalid varint length")
                                
                                if pos + length <= len(data) and length > 0 and length <= 32:
                                    instance_uid_bytes = data[pos:pos+length]
                                    agent_message.instance_uid = instance_uid_bytes
                                    instance_uid_found = True
                                    logger.warning(f"Extracted instance_uid from unparseable message: {instance_uid_bytes.hex()}")
                                    break
                        
                        # Skip unknown fields based on wire type
                        wire_type = tag & 0x07
                        field_number = tag >> 3
                        
                        if wire_type == 0:  # Varint
                            while pos < len(data) and (data[pos] & 0x80):
                                pos += 1
                            if pos < len(data):
                                pos += 1
                        elif wire_type == 1:  # Fixed64
                            pos += 8
                        elif wire_type == 2:  # Length-delimited
                            if pos < len(data):
                                # Read varint length
                                length = 0
                                shift = 0
                                while pos < len(data):
                                    byte = data[pos]
                                    pos += 1
                                    length |= (byte & 0x7F) << shift
                                    if not (byte & 0x80):
                                        break
                                    shift += 7
                                    if shift >= 32:
                                        raise ValueError("Invalid varint length")
                                pos += length
                        elif wire_type == 5:  # Fixed32
                            pos += 4
                        else:
                            break
                        
                        if pos >= len(data):
                            break
                    
                    # If we couldn't extract instance_uid, this message is truly unparseable
                    if not instance_uid_found or not agent_message.instance_uid:
                        raise merge_error
                    
                    logger.warning(
                        f"Partially parsed AgentToServer message (extracted instance_uid only) "
                        f"after both ParseFromString and MergeFromString failed. "
                        f"Full parse errors: ParseFromString={e}, MergeFromString={merge_error} "
                        f"(message size: {len(data)} bytes). "
                        f"This may indicate a protobuf version mismatch or unknown fields."
                    )
                    return agent_message
                except Exception as extract_error:
                    # All parsing methods failed - log detailed error
                    # Use module-level logger (already imported at top of file)
                    logger.error(
                        f"CRITICAL: Failed to parse AgentToServer message with all methods: "
                        f"ParseFromString={e}, MergeFromString={merge_error}, ManualExtract={extract_error} "
                        f"(message size: {len(data) if data else 0} bytes). "
                        f"This message will be SKIPPED to avoid incorrect capability inference. "
                        f"First 100 bytes (hex): {data[:100].hex() if len(data) >= 100 else data.hex()}"
                    )
                    # Return None to signal that this message should not be processed
                    # The caller should check for None and skip processing
                    return None
    
    def _dict_to_agent_message(self, data: Dict[str, Any], msg: opamp_pb2.AgentToServer):
        """Convert dictionary (from Go parser) to AgentToServer protobuf message"""
        import base64
        if "instance_uid" in data:
            uid = data["instance_uid"]
            if isinstance(uid, str):
                # Try base64 decode if it's a string
                try:
                    msg.instance_uid = base64.b64decode(uid)
                except:
                    msg.instance_uid = uid.encode('utf-8')
            elif isinstance(uid, bytes):
                msg.instance_uid = uid
            elif isinstance(uid, list):
                # JSON array of bytes
                msg.instance_uid = bytes(uid)
        if "sequence_num" in data:
            msg.sequence_num = int(data["sequence_num"])
        if "capabilities" in data:
            capabilities_value = data["capabilities"]
            # Handle different types (int, float, string)
            if isinstance(capabilities_value, float):
                capabilities_value = int(capabilities_value)
            elif isinstance(capabilities_value, str):
                # Try to parse hex string if provided
                if capabilities_value.startswith("0x") or capabilities_value.startswith("0X"):
                    capabilities_value = int(capabilities_value, 16)
                else:
                    capabilities_value = int(capabilities_value)
            else:
                capabilities_value = int(capabilities_value)
            msg.capabilities = capabilities_value
            logger.debug(f"[OpAMP] Set capabilities from dict: 0x{msg.capabilities:X} ({msg.capabilities})")
        if "flags" in data:
            msg.flags = int(data["flags"])
        # Add more field mappings as needed - for now, just the essential fields
    
    def serialize_server_message(self, message: opamp_pb2.ServerToAgent) -> bytes:
        """
        Serialize ServerToAgent Protobuf message to bytes
        
        Args:
            message: ServerToAgent Protobuf message
        
        Returns:
            Serialized message as bytes (Protobuf wire format)
        """
        return message.SerializeToString()
    
    def create_error_response(
        self,
        error_type: int = opamp_pb2.ServerErrorResponseType_Unknown,
        error_message: str = "Unknown error"
    ) -> opamp_pb2.ServerToAgent:
        """
        Create a ServerToAgent error response message
        
        Args:
            error_type: ServerErrorResponseType enum value
            error_message: Human-readable error message
        
        Returns:
            ServerToAgent message with error_response set
        """
        error_response = opamp_pb2.ServerErrorResponse()
        error_response.type = error_type
        error_response.error_message = error_message
        
        server_message = opamp_pb2.ServerToAgent()
        server_message.error_response.CopyFrom(error_response)
        
        return server_message

