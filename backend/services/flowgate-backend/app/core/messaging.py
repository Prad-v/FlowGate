"""NATS messaging client for event streaming"""

import json
import logging
from typing import Optional, Callable, Dict, Any
from contextlib import asynccontextmanager
import nats
from nats.aio.client import Client as NATS
from nats.aio.subscription import Subscription
from app.config import settings

logger = logging.getLogger(__name__)


class NATSClient:
    """NATS client wrapper for event publishing and subscription"""
    
    def __init__(self):
        self._nc: Optional[NATS] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to NATS server"""
        if self._connected and self._nc:
            return
        
        try:
            self._nc = await nats.connect(
                servers=[settings.nats_url],
                reconnect_time_wait=2,
                max_reconnect_attempts=10,
                connect_timeout=5,
            )
            self._connected = True
            logger.info(f"Connected to NATS server at {settings.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from NATS server"""
        if self._nc:
            await self._nc.close()
            self._connected = False
            logger.info("Disconnected from NATS server")
    
    async def publish(
        self,
        subject: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Publish a message to a NATS subject"""
        if not self._connected or not self._nc:
            await self.connect()
        
        try:
            message_data = json.dumps(data).encode('utf-8')
            await self._nc.publish(subject, message_data, headers=headers)
            logger.debug(f"Published message to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish message to {subject}: {e}")
            raise
    
    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Dict[str, Any], str], None],
        queue: Optional[str] = None
    ) -> Subscription:
        """Subscribe to a NATS subject"""
        if not self._connected or not self._nc:
            await self.connect()
        
        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode('utf-8'))
                await callback(data, msg.subject)
            except Exception as e:
                logger.error(f"Error processing message from {msg.subject}: {e}")
        
        try:
            sub = await self._nc.subscribe(
                subject,
                cb=message_handler,
                queue=queue
            )
            logger.info(f"Subscribed to {subject}" + (f" (queue: {queue})" if queue else ""))
            return sub
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject}: {e}")
            raise
    
    async def request(
        self,
        subject: str,
        data: Dict[str, Any],
        timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response"""
        if not self._connected or not self._nc:
            await self.connect()
        
        try:
            message_data = json.dumps(data).encode('utf-8')
            response = await self._nc.request(subject, message_data, timeout=timeout)
            return json.loads(response.data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to send request to {subject}: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Check if connected to NATS"""
        return self._connected and self._nc is not None


# Global NATS client instance
_nats_client: Optional[NATSClient] = None


def get_nats_client() -> NATSClient:
    """Get or create global NATS client instance"""
    global _nats_client
    if _nats_client is None:
        _nats_client = NATSClient()
    return _nats_client


async def init_nats() -> None:
    """Initialize NATS connection (call on app startup)"""
    client = get_nats_client()
    await client.connect()


async def close_nats() -> None:
    """Close NATS connection (call on app shutdown)"""
    client = get_nats_client()
    await client.disconnect()


def format_log_subject(source_type: str, org_id: str) -> str:
    """Format NATS subject for normalized logs"""
    return f"logs.normalized.{source_type}.{org_id}"

