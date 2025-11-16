"""Connection Settings Service for OpAMP connection credential management"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.connection_settings import (
    ConnectionSettings,
    ConnectionSettingsType,
    ConnectionSettingsStatus
)
from app.models.gateway import Gateway
import hashlib
import logging
import base64

logger = logging.getLogger(__name__)


class ConnectionSettingsService:
    """Service for managing OpAMP connection settings"""

    def __init__(self, db: Session):
        self.db = db

    def get_connection_settings_for_gateway(
        self, gateway_id: UUID, org_id: UUID, settings_type: Optional[ConnectionSettingsType] = None
    ) -> List[ConnectionSettings]:
        """Get connection settings for a gateway"""
        query = self.db.query(ConnectionSettings).filter(
            and_(
                ConnectionSettings.gateway_id == gateway_id,
                ConnectionSettings.org_id == org_id
            )
        )
        if settings_type:
            query = query.filter(ConnectionSettings.settings_type == settings_type)
        return query.all()

    def get_connection_setting(
        self, setting_id: UUID, org_id: UUID
    ) -> Optional[ConnectionSettings]:
        """Get a connection setting by ID"""
        return self.db.query(ConnectionSettings).filter(
            and_(
                ConnectionSettings.id == setting_id,
                ConnectionSettings.org_id == org_id
            )
        ).first()

    def create_connection_setting(
        self,
        gateway_id: UUID,
        org_id: UUID,
        settings_type: ConnectionSettingsType,
        settings_data: Dict[str, Any],
        settings_name: Optional[str] = None,
        certificate_pem: Optional[str] = None,
        private_key_pem: Optional[str] = None,
        ca_cert_pem: Optional[str] = None,
    ) -> ConnectionSettings:
        """Create connection settings for a gateway"""
        # Calculate settings hash
        settings_hash = self._calculate_settings_hash(settings_data, certificate_pem)

        # Check if settings already exist
        existing = self.db.query(ConnectionSettings).filter(
            and_(
                ConnectionSettings.gateway_id == gateway_id,
                ConnectionSettings.settings_type == settings_type,
                ConnectionSettings.settings_name == settings_name,
                ConnectionSettings.org_id == org_id
            )
        ).first()

        if existing:
            # Update existing settings
            existing.settings_data = settings_data
            existing.settings_hash = settings_hash
            existing.certificate_pem = certificate_pem
            existing.private_key_pem = private_key_pem
            existing.ca_cert_pem = ca_cert_pem
            existing.status = ConnectionSettingsStatus.UNSET  # Reset status
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        setting = ConnectionSettings(
            gateway_id=gateway_id,
            org_id=org_id,
            settings_type=settings_type,
            settings_name=settings_name,
            settings_data=settings_data,
            settings_hash=settings_hash,
            certificate_pem=certificate_pem,
            private_key_pem=private_key_pem,
            ca_cert_pem=ca_cert_pem,
            status=ConnectionSettingsStatus.UNSET,
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def update_connection_setting_status(
        self,
        gateway_id: UUID,
        settings_hash: str,
        status: ConnectionSettingsStatus,
        error_message: Optional[str] = None,
    ) -> Optional[ConnectionSettings]:
        """Update connection settings status from agent report"""
        setting = self.db.query(ConnectionSettings).filter(
            and_(
                ConnectionSettings.gateway_id == gateway_id,
                ConnectionSettings.settings_hash == settings_hash
            )
        ).first()

        if not setting:
            logger.warning(f"Connection settings with hash {settings_hash} not found for gateway {gateway_id}")
            return None

        setting.status = status
        if error_message:
            setting.error_message = error_message
        if status == ConnectionSettingsStatus.APPLIED:
            setting.applied_at = datetime.utcnow()
        elif status == ConnectionSettingsStatus.FAILED:
            setting.error_message = error_message or "Connection settings application failed"

        setting.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def handle_csr_request(
        self,
        gateway_id: UUID,
        org_id: UUID,
        csr_pem: str,
    ) -> Optional[ConnectionSettings]:
        """Handle Certificate Signing Request from agent"""
        # TODO: Implement proper CSR handling
        # This should:
        # 1. Validate the CSR
        # 2. Sign the certificate using CA
        # 3. Create connection settings with the signed certificate
        # 4. Return the connection settings

        logger.warning("CSR handling not yet fully implemented")
        
        # For now, create a placeholder connection setting
        # In production, this should generate a proper certificate
        setting = ConnectionSettings(
            gateway_id=gateway_id,
            org_id=org_id,
            settings_type=ConnectionSettingsType.OPAMP,
            csr_pem=csr_pem,
            status=ConnectionSettingsStatus.UNSET,
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def get_connection_settings_offers_for_gateway(
        self, gateway_id: UUID, org_id: UUID
    ) -> Dict[str, Any]:
        """Get connection settings that should be offered to a gateway"""
        settings = self.get_connection_settings_for_gateway(gateway_id, org_id)
        
        result = {
            "opamp": None,
            "own_metrics": None,
            "own_traces": None,
            "own_logs": None,
            "other_connections": {},
        }

        for setting in settings:
            if setting.status == ConnectionSettingsStatus.UNSET:
                settings_dict = self._convert_to_opamp_format(setting)
                if setting.settings_type == ConnectionSettingsType.OPAMP:
                    result["opamp"] = settings_dict
                elif setting.settings_type == ConnectionSettingsType.OWN_METRICS:
                    result["own_metrics"] = settings_dict
                elif setting.settings_type == ConnectionSettingsType.OWN_TRACES:
                    result["own_traces"] = settings_dict
                elif setting.settings_type == ConnectionSettingsType.OWN_LOGS:
                    result["own_logs"] = settings_dict
                elif setting.settings_type == ConnectionSettingsType.OTHER:
                    if setting.settings_name:
                        result["other_connections"][setting.settings_name] = settings_dict

        return result

    def _convert_to_opamp_format(self, setting: ConnectionSettings) -> Dict[str, Any]:
        """Convert connection setting to OpAMP format"""
        result = {}
        
        if setting.settings_data:
            result.update(setting.settings_data)
        
        # Add TLS settings if certificates are present
        if setting.certificate_pem or setting.ca_cert_pem:
            tls_settings = {}
            if setting.certificate_pem:
                tls_settings["cert"] = setting.certificate_pem.encode() if isinstance(setting.certificate_pem, str) else setting.certificate_pem
            if setting.private_key_pem:
                tls_settings["key"] = setting.private_key_pem.encode() if isinstance(setting.private_key_pem, str) else setting.private_key_pem
            if setting.ca_cert_pem:
                tls_settings["ca_cert"] = setting.ca_cert_pem.encode() if isinstance(setting.ca_cert_pem, str) else setting.ca_cert_pem
            result["tls"] = tls_settings
        
        return result

    def _calculate_settings_hash(
        self, settings_data: Dict[str, Any], certificate_pem: Optional[str] = None
    ) -> str:
        """Calculate hash for connection settings"""
        import json
        hash_input = json.dumps(settings_data, sort_keys=True)
        if certificate_pem:
            hash_input += certificate_pem
        return hashlib.sha256(hash_input.encode()).hexdigest()

