"""Tests for Threat Detection Service (NATS integration)"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.threat_detection_service import ThreatDetectionService
from app.core.messaging import NATSClient, get_nats_client


class TestThreatDetectionService:
    """Test suite for Threat Detection Service"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def threat_detection_service(self, mock_db):
        """Create Threat Detection Service instance"""
        with patch('app.services.threat_detection_service.ThreatVectorService') as mock_tva:
            mock_tva_instance = Mock()
            mock_tva_instance.analyze_log = AsyncMock(return_value=None)
            mock_tva.return_value = mock_tva_instance
            
            service = ThreatDetectionService(mock_db)
            # Mock NATS client
            mock_nats = AsyncMock()
            mock_nats.connect = AsyncMock()
            mock_nats.subscribe = AsyncMock(return_value=Mock())
            mock_nats.close = AsyncMock()
            service.nats_client = mock_nats
            return service

    @pytest.mark.asyncio
    async def test_start_service(self, threat_detection_service):
        """Test starting the threat detection service"""
        await threat_detection_service.start()
        
        assert threat_detection_service._running is True
        threat_detection_service.nats_client.connect.assert_called_once()
        threat_detection_service.nats_client.subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_service(self, threat_detection_service):
        """Test stopping the threat detection service"""
        threat_detection_service._running = True
        threat_detection_service._subscriptions = [Mock()]
        
        with patch.object(threat_detection_service._subscriptions[0], 'unsubscribe', new_callable=AsyncMock):
            await threat_detection_service.stop()
            
            assert threat_detection_service._running is False
            assert len(threat_detection_service._subscriptions) == 0

    @pytest.mark.asyncio
    async def test_process_normalized_log(self, threat_detection_service):
        """Test processing a normalized log message"""
        test_data = {
            "source": "identity",
            "org_id": "test-org-123",
            "log_data": "User login event",
            "metadata": {"entity_id": "user123"}
        }
        
        await threat_detection_service._process_normalized_log(test_data, "logs.normalized.identity.test-org")
        
        # Verify TVA was called
        threat_detection_service.threat_vector_service.analyze_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_normalized_log_no_org_id(self, threat_detection_service):
        """Test processing log without org_id (should skip)"""
        test_data = {
            "source": "identity",
            "log_data": "User login event"
        }
        
        # Should not raise error, just skip processing
        await threat_detection_service._process_normalized_log(test_data, "logs.normalized.identity")
        
        # TVA should not be called
        threat_detection_service.threat_vector_service.analyze_log.assert_not_called()


class TestNATSClient:
    """Test suite for NATS Client"""

    @pytest.fixture
    def nats_client(self):
        """Create NATS client instance"""
        return NATSClient()

    @pytest.mark.asyncio
    async def test_connect(self, nats_client):
        """Test connecting to NATS"""
        with patch('nats.connect', new_callable=AsyncMock) as mock_connect:
            mock_nc = Mock()
            mock_connect.return_value = mock_nc
            
            await nats_client.connect()
            
            assert nats_client.is_connected() is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish(self, nats_client):
        """Test publishing a message"""
        mock_nc = Mock()
        mock_nc.publish = AsyncMock()
        nats_client._nc = mock_nc
        nats_client._connected = True
        
        message = {"test": "data"}
        await nats_client.publish("test.subject", message)
        
        mock_nc.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe(self, nats_client):
        """Test subscribing to a subject"""
        mock_nc = Mock()
        mock_sub = Mock()
        mock_nc.subscribe = AsyncMock(return_value=mock_sub)
        nats_client._nc = mock_nc
        nats_client._connected = True
        
        callback = AsyncMock()
        subscription = await nats_client.subscribe("test.subject", callback)
        
        assert subscription == mock_sub
        mock_nc.subscribe.assert_called_once()

