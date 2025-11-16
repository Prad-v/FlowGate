"""WebSocket connection manager for OpAMP connections"""

import logging
from typing import Dict, Optional
from fastapi import WebSocket
from app.protobufs import opamp_pb2

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections for OpAMP agents
    
    Allows immediate message sending to connected agents without waiting
    for the next message exchange cycle.
    """
    
    def __init__(self):
        # Map instance_id -> WebSocket connection
        self._connections: Dict[str, WebSocket] = {}
    
    def register_connection(self, instance_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for an instance
        
        Args:
            instance_id: Gateway instance identifier
            websocket: WebSocket connection object
        """
        self._connections[instance_id] = websocket
        logger.info(f"Registered WebSocket connection for instance: {instance_id}")
    
    def unregister_connection(self, instance_id: str) -> None:
        """Unregister a WebSocket connection for an instance
        
        Args:
            instance_id: Gateway instance identifier
        """
        if instance_id in self._connections:
            del self._connections[instance_id]
            logger.info(f"Unregistered WebSocket connection for instance: {instance_id}")
    
    def get_connection(self, instance_id: str) -> Optional[WebSocket]:
        """Get WebSocket connection for an instance
        
        Args:
            instance_id: Gateway instance identifier
        
        Returns:
            WebSocket connection if exists, None otherwise
        """
        return self._connections.get(instance_id)
    
    def is_connected(self, instance_id: str) -> bool:
        """Check if instance has an active WebSocket connection
        
        Args:
            instance_id: Gateway instance identifier
        
        Returns:
            True if connected, False otherwise
        """
        return instance_id in self._connections
    
    async def send_message(self, instance_id: str, message: opamp_pb2.ServerToAgent, message_bytes: bytes) -> bool:
        """Send a message to a connected instance
        
        Args:
            instance_id: Gateway instance identifier
            message: ServerToAgent protobuf message
            message_bytes: Serialized message bytes
        
        Returns:
            True if message was sent, False if instance not connected
        """
        websocket = self.get_connection(instance_id)
        if not websocket:
            logger.warning(f"No WebSocket connection for instance: {instance_id}")
            return False
        
        try:
            await websocket.send_bytes(message_bytes)
            logger.debug(f"Sent message to instance {instance_id} via WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to instance {instance_id}: {e}", exc_info=True)
            # Remove connection if send failed
            self.unregister_connection(instance_id)
            return False
    
    def get_connected_instances(self) -> list[str]:
        """Get list of all connected instance IDs
        
        Returns:
            List of instance IDs with active connections
        """
        return list(self._connections.keys())


# Global singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

