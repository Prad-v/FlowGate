"""Gateway repository"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.gateway import Gateway
from app.repositories.base_repository import BaseRepository


class GatewayRepository(BaseRepository[Gateway]):
    """Repository for Gateway operations"""

    def __init__(self, db: Session):
        super().__init__(Gateway, db)

    def get_by_instance_id(self, instance_id: str) -> Optional[Gateway]:
        """Get gateway by OpAMP instance ID"""
        return (
            self.db.query(Gateway)
            .filter(Gateway.instance_id == instance_id)
            .first()
        )

    def get_active_gateways(self, org_id: UUID) -> List[Gateway]:
        """Get all active gateways for an organization"""
        from app.models.gateway import GatewayStatus
        return (
            self.db.query(Gateway)
            .filter(
                Gateway.org_id == org_id,
                Gateway.status == GatewayStatus.ACTIVE,
            )
            .all()
        )

    def update_last_seen(self, gateway_id: UUID) -> Optional[Gateway]:
        """Update gateway's last_seen timestamp"""
        from datetime import datetime
        gateway = self.get(gateway_id)
        if gateway:
            gateway.last_seen = datetime.utcnow()
            self.db.commit()
            self.db.refresh(gateway)
        return gateway

