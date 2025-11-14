"""Gateway repository."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.gateway import Gateway
from repositories.base import BaseRepository


class GatewayRepository(BaseRepository[Gateway]):
    """Repository for Gateway operations."""
    
    def __init__(self, db: Session):
        """Initialize gateway repository."""
        super().__init__(Gateway, db)
        self.db = db
    
    def get_by_instance_id(
        self,
        instance_id: str,
        org_id: Optional[UUID] = None
    ) -> Optional[Gateway]:
        """Get gateway by instance ID."""
        query = self.db.query(Gateway).filter(Gateway.instance_id == instance_id)
        if org_id:
            query = query.filter(Gateway.org_id == org_id)
        return query.first()
    
    def update_heartbeat(
        self,
        instance_id: str,
        status: str = "online",
        org_id: Optional[UUID] = None
    ) -> Optional[Gateway]:
        """Update gateway heartbeat."""
        gateway = self.get_by_instance_id(instance_id, org_id)
        if not gateway:
            return None
        gateway.last_seen = datetime.utcnow()
        gateway.status = status
        self.db.commit()
        self.db.refresh(gateway)
        return gateway
    
    def get_online_gateways(self, org_id: Optional[UUID] = None) -> List[Gateway]:
        """Get all online gateways."""
        query = self.db.query(Gateway).filter(Gateway.status == "online")
        if org_id:
            query = query.filter(Gateway.org_id == org_id)
        return query.all()


