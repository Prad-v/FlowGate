"""Session service for managing user sessions"""

import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions (stored in Redis)"""

    def __init__(self):
        self.redis_client = None
        if settings.redis_url:
            try:
                self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Sessions will not be persisted.")
        self.session_ttl = timedelta(days=7)  # 7 days session expiration

    def create_session(self, user_id: UUID, org_id: Optional[UUID], user_data: Dict[str, Any]) -> str:
        """
        Create a new session
        
        Args:
            user_id: User UUID
            org_id: Organization UUID (optional)
            user_data: Additional user data to store in session
        
        Returns:
            Session ID string
        """
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": str(user_id),
            "org_id": str(org_id) if org_id else None,
            "created_at": datetime.utcnow().isoformat(),
            **user_data
        }
        
        if self.redis_client:
            # Store in Redis with TTL
            import json
            self.redis_client.setex(
                f"session:{session_id}",
                int(self.session_ttl.total_seconds()),
                json.dumps(session_data)
            )
        else:
            # Fallback: store in memory (not recommended for production)
            logger.warning("Redis not available, sessions will not persist across restarts")
        
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by session ID
        
        Args:
            session_id: Session ID string
        
        Returns:
            Session data dictionary or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            import json
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
        except Exception as e:
            logger.error(f"Error getting session: {e}")
        
        return None

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session
        
        Args:
            session_id: Session ID string
        """
        if self.redis_client:
            try:
                self.redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.error(f"Error deleting session: {e}")

    def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session expiration time
        
        Args:
            session_id: Session ID string
        
        Returns:
            True if session was refreshed, False if session not found
        """
        if not self.redis_client:
            return False
        
        try:
            # Get current session
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            # Update expiration
            import json
            self.redis_client.setex(
                f"session:{session_id}",
                int(self.session_ttl.total_seconds()),
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            logger.error(f"Error refreshing session: {e}")
            return False


# Global session service instance
_session_service = None


def get_session_service() -> SessionService:
    """Get global session service instance"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service

