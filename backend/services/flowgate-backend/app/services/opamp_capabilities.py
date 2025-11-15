"""OpAMP Capabilities - Bit-field definitions and negotiation logic

Based on OpAMP specification: https://opentelemetry.io/docs/specs/opamp/
"""

from typing import Dict, Set, List


# Agent Capabilities (bit positions per OpAMP spec)
class AgentCapabilities:
    """Agent capabilities as defined in OpAMP specification"""
    
    # Capability bit positions (per OpAMP spec)
    REPORTS_STATUS = 0  # 0x01
    ACCEPTS_REMOTE_CONFIG = 1  # 0x02
    REPORTS_EFFECTIVE_CONFIG = 2  # 0x04
    ACCEPTS_PACKAGES = 3  # 0x08
    REPORTS_PACKAGE_STATUSES = 4  # 0x10
    REPORTS_OWN_TRACES = 5  # 0x20
    REPORTS_OWN_METRICS = 6  # 0x40
    REPORTS_OWN_LOGS = 7  # 0x80
    ACCEPTS_OPAMP_CONNECTION_SETTINGS = 8  # 0x100
    ACCEPTS_OTHER_CONNECTION_SETTINGS = 9  # 0x200
    ACCEPTS_RESTART_COMMAND = 10  # 0x400
    REPORTS_HEALTH = 11  # 0x800
    REPORTS_REMOTE_CONFIG = 12  # 0x1000
    REPORTS_HEARTBEAT = 13  # 0x2000
    REPORTS_AVAILABLE_COMPONENTS = 14  # 0x4000
    REPORTS_CONNECTION_SETTINGS_STATUS = 15  # 0x8000
    
    # Capability names mapping (bit position -> name)
    NAMES = {
        REPORTS_STATUS: "ReportsStatus",
        ACCEPTS_REMOTE_CONFIG: "AcceptsRemoteConfig",
        REPORTS_EFFECTIVE_CONFIG: "ReportsEffectiveConfig",
        ACCEPTS_PACKAGES: "AcceptsPackages",
        REPORTS_PACKAGE_STATUSES: "ReportsPackageStatuses",
        REPORTS_OWN_TRACES: "ReportsOwnTraces",
        REPORTS_OWN_METRICS: "ReportsOwnMetrics",
        REPORTS_OWN_LOGS: "ReportsOwnLogs",
        ACCEPTS_OPAMP_CONNECTION_SETTINGS: "AcceptsOpAMPConnectionSettings",
        ACCEPTS_OTHER_CONNECTION_SETTINGS: "AcceptsOtherConnectionSettings",
        ACCEPTS_RESTART_COMMAND: "AcceptsRestartCommand",
        REPORTS_HEALTH: "ReportsHealth",
        REPORTS_REMOTE_CONFIG: "ReportsRemoteConfig",
        REPORTS_HEARTBEAT: "ReportsHeartbeat",
        REPORTS_AVAILABLE_COMPONENTS: "ReportsAvailableComponents",
        REPORTS_CONNECTION_SETTINGS_STATUS: "ReportsConnectionSettingsStatus",
    }
    
    @staticmethod
    def to_bit_field(capabilities: Set[int]) -> int:
        """Convert set of capability indices to bit-field"""
        bit_field = 0
        for cap in capabilities:
            bit_field |= (1 << cap)
        return bit_field
    
    @staticmethod
    def from_bit_field(bit_field: int) -> Set[int]:
        """Convert bit-field to set of capability indices"""
        capabilities = set()
        for i in range(64):  # Support up to 64 capabilities
            if bit_field & (1 << i):
                capabilities.add(i)
        return capabilities
    
    @staticmethod
    def get_all_capabilities() -> int:
        """Get bit-field with all standard capabilities enabled"""
        return AgentCapabilities.to_bit_field({
            AgentCapabilities.REPORTS_STATUS,
            AgentCapabilities.ACCEPTS_REMOTE_CONFIG,
            AgentCapabilities.REPORTS_EFFECTIVE_CONFIG,
            AgentCapabilities.REPORTS_HEALTH,
        })
    
    @staticmethod
    def decode_capabilities(bit_field: int) -> List[str]:
        """
        Decode agent capabilities bit-field to list of capability names
        
        Args:
            bit_field: Capabilities bit-field value
        
        Returns:
            List of capability names
        """
        capabilities = AgentCapabilities.from_bit_field(bit_field)
        return [AgentCapabilities.NAMES.get(bit_pos, f"Unknown({bit_pos})") 
                for bit_pos in sorted(capabilities)]


# Server Capabilities (bit positions per OpAMP spec)
class ServerCapabilities:
    """Server capabilities as defined in OpAMP specification"""
    
    # Capability bit positions (per OpAMP spec)
    ACCEPTS_STATUS = 0  # 0x01
    OFFERS_REMOTE_CONFIG = 1  # 0x02
    ACCEPTS_EFFECTIVE_CONFIG = 2  # 0x04
    OFFERS_PACKAGES = 3  # 0x08
    ACCEPTS_PACKAGES_STATUS = 4  # 0x10
    OFFERS_CONNECTION_SETTINGS = 5  # 0x20
    ACCEPTS_CONNECTION_SETTINGS_REQUEST = 6  # 0x40
    
    # Capability names mapping (bit position -> name)
    NAMES = {
        ACCEPTS_STATUS: "AcceptsStatus",
        OFFERS_REMOTE_CONFIG: "OffersRemoteConfig",
        ACCEPTS_EFFECTIVE_CONFIG: "AcceptsEffectiveConfig",
        OFFERS_PACKAGES: "OffersPackages",
        ACCEPTS_PACKAGES_STATUS: "AcceptsPackagesStatus",
        OFFERS_CONNECTION_SETTINGS: "OffersConnectionSettings",
        ACCEPTS_CONNECTION_SETTINGS_REQUEST: "AcceptsConnectionSettingsRequest",
    }
    
    @staticmethod
    def to_bit_field(capabilities: Set[int]) -> int:
        """Convert set of capability indices to bit-field"""
        bit_field = 0
        for cap in capabilities:
            bit_field |= (1 << cap)
        return bit_field
    
    @staticmethod
    def from_bit_field(bit_field: int) -> Set[int]:
        """Convert bit-field to set of capability indices"""
        capabilities = set()
        for i in range(64):  # Support up to 64 capabilities
            if bit_field & (1 << i):
                capabilities.add(i)
        return capabilities
    
    @staticmethod
    def get_all_capabilities() -> int:
        """Get bit-field with all standard capabilities enabled"""
        return ServerCapabilities.to_bit_field({
            ServerCapabilities.ACCEPTS_STATUS,
            ServerCapabilities.OFFERS_REMOTE_CONFIG,
            ServerCapabilities.ACCEPTS_EFFECTIVE_CONFIG,
        })
    
    @staticmethod
    def decode_capabilities(bit_field: int) -> List[str]:
        """
        Decode server capabilities bit-field to list of capability names
        
        Args:
            bit_field: Capabilities bit-field value
        
        Returns:
            List of capability names
        """
        capabilities = ServerCapabilities.from_bit_field(bit_field)
        return [ServerCapabilities.NAMES.get(bit_pos, f"Unknown({bit_pos})") 
                for bit_pos in sorted(capabilities)]


def negotiate_capabilities(
    agent_capabilities: int,
    server_capabilities: int
) -> Dict[str, int]:
    """
    Negotiate capabilities between agent and server
    
    Returns:
        Dict with 'agent' and 'server' keys containing negotiated capabilities
    """
    agent_caps = AgentCapabilities.from_bit_field(agent_capabilities)
    server_caps = ServerCapabilities.from_bit_field(server_capabilities)
    
    # Server should only use capabilities that the agent supports
    # Agent should only use capabilities that the server supports
    
    # For now, return intersection of capabilities
    # In practice, this would be more sophisticated based on the spec
    
    return {
        "agent": agent_capabilities,  # Agent reports what it supports
        "server": server_capabilities,  # Server reports what it supports
    }


def format_capabilities_display(bit_field: int, decoded: List[str]) -> Dict[str, any]:
    """
    Format capabilities for UI display
    
    Args:
        bit_field: Capabilities bit-field value
        decoded: List of decoded capability names
    
    Returns:
        Dict with bit_field (hex), bit_field_decimal, and names
    """
    return {
        "bit_field_hex": f"0x{bit_field:X}",
        "bit_field_decimal": bit_field,
        "names": decoded,
    }

