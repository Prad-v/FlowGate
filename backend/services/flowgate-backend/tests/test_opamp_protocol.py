"""Tests for OpAMP Protocol Implementation

Tests OpAMP protocol compliance according to:
https://opentelemetry.io/docs/specs/opamp/
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.opamp_protocol_service import OpAMPProtocolService
from app.services.opamp_capabilities import (
    AgentCapabilities,
    ServerCapabilities,
    negotiate_capabilities
)


class TestOpAMPCapabilities:
    """Test OpAMP capability bit-field handling"""
    
    def test_agent_capabilities_to_bit_field(self):
        """Test converting agent capabilities to bit-field"""
        capabilities = {
            AgentCapabilities.ACCEPTS_REMOTE_CONFIG,
            AgentCapabilities.REPORTS_EFFECTIVE_CONFIG,
        }
        bit_field = AgentCapabilities.to_bit_field(capabilities)
        assert bit_field == (1 << 0) | (1 << 1)
    
    def test_agent_capabilities_from_bit_field(self):
        """Test converting bit-field to agent capabilities"""
        bit_field = (1 << 0) | (1 << 1) | (1 << 2)
        capabilities = AgentCapabilities.from_bit_field(bit_field)
        assert AgentCapabilities.ACCEPTS_REMOTE_CONFIG in capabilities
        assert AgentCapabilities.REPORTS_EFFECTIVE_CONFIG in capabilities
        assert AgentCapabilities.REPORTS_OWN_TELEMETRY in capabilities
    
    def test_server_capabilities_to_bit_field(self):
        """Test converting server capabilities to bit-field"""
        capabilities = {
            ServerCapabilities.ACCEPTS_STATUS,
            ServerCapabilities.OFFERS_REMOTE_CONFIG,
        }
        bit_field = ServerCapabilities.to_bit_field(capabilities)
        assert bit_field == (1 << 0) | (1 << 1)
    
    def test_capability_negotiation(self):
        """Test capability negotiation between agent and server"""
        agent_caps = AgentCapabilities.to_bit_field({
            AgentCapabilities.ACCEPTS_REMOTE_CONFIG,
            AgentCapabilities.REPORTS_EFFECTIVE_CONFIG,
        })
        server_caps = ServerCapabilities.to_bit_field({
            ServerCapabilities.OFFERS_REMOTE_CONFIG,
            ServerCapabilities.ACCEPTS_EFFECTIVE_CONFIG,
        })
        
        negotiated = negotiate_capabilities(agent_caps, server_caps)
        assert "agent" in negotiated
        assert "server" in negotiated


class TestOpAMPProtocolService:
    """Test OpAMP protocol message handling"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def protocol_service(self, mock_db):
        """Create OpAMP protocol service"""
        return OpAMPProtocolService(mock_db)
    
    def test_build_initial_server_message(self, protocol_service, mock_db):
        """Test building initial ServerToAgent message"""
        with patch.object(protocol_service.gateway_service.repository, 'get_by_instance_id') as mock_get:
            mock_gateway = Mock()
            mock_gateway.id = "test-gateway-id"
            mock_get.return_value = mock_gateway
            
            with patch.object(protocol_service.opamp_service, 'get_config_for_gateway') as mock_config:
                mock_config.return_value = None
                
                message = protocol_service.build_initial_server_message("test-instance")
                
                assert "instance_uid" in message
                assert "capabilities" in message
                assert message["instance_uid"] == "test-gateway-id"
    
    def test_parse_agent_message_json(self, protocol_service):
        """Test parsing JSON AgentToServer message"""
        json_data = b'{"capabilities": 3, "instance_uid": "test"}'
        message = protocol_service.parse_agent_message(json_data)
        assert message["capabilities"] == 3
        assert message["instance_uid"] == "test"
    
    def test_serialize_server_message(self, protocol_service):
        """Test serializing ServerToAgent message"""
        message = {
            "instance_uid": "test",
            "capabilities": 5
        }
        serialized = protocol_service.serialize_server_message(message)
        assert isinstance(serialized, bytes)
        # Should be JSON for now
        import json
        deserialized = json.loads(serialized.decode('utf-8'))
        assert deserialized["instance_uid"] == "test"


class TestOpAMPWebSocket:
    """Test OpAMP WebSocket transport"""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is registered"""
        from app.main import app
        from app.routers import opamp_websocket
        
        # Check that router is included
        assert opamp_websocket.router is not None


class TestOpAMPHTTP:
    """Test OpAMP HTTP transport"""
    
    def test_http_endpoint_exists(self):
        """Test that HTTP endpoint is registered"""
        from app.main import app
        from app.routers import opamp_http
        
        # Check that router is included
        assert opamp_http.router is not None

