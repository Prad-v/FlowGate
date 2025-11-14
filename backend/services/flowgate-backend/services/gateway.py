"""Gateway service."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from models.gateway import Gateway
from repositories.gateway import GatewayRepository
from schemas.gateway import GatewayCreate, GatewayUpdate, GatewayHeartbeat, GatewayResponse


class GatewayService:
    """Service for gateway operations."""
    
    def __init__(self, db: Session):
        """Initialize gateway service."""
        self.db = db
        self.repo = GatewayRepository(db)
    
    def register_gateway(
        self,
        org_id: UUID,
        gateway_data: GatewayCreate
    ) -> Gateway:
        """Register a new gateway."""
        # Check if gateway already exists
        existing = self.repo.get_by_instance_id(gateway_data.instance_id, org_id)
        if existing:
            # Update existing gateway
            existing.name = gateway_data.name
            existing.hostname = gateway_data.hostname
            existing.ip_address = gateway_data.ip_address
            existing.version = gateway_data.version
            existing.metadata = gateway_data.metadata
            existing.status = "online"
            existing.last_seen = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new gateway
        gateway = Gateway(
            org_id=org_id,
            name=gateway_data.name,
            instance_id=gateway_data.instance_id,
            hostname=gateway_data.hostname,
            ip_address=gateway_data.ip_address,
            version=gateway_data.version,
            status="online",
            last_seen=datetime.utcnow(),
            metadata=gateway_data.metadata
        )
        return self.repo.create(gateway)
    
    def update_heartbeat(
        self,
        instance_id: str,
        heartbeat: GatewayHeartbeat,
        org_id: Optional[UUID] = None
    ) -> Optional[Gateway]:
        """Update gateway heartbeat."""
        gateway = self.repo.get_by_instance_id(instance_id, org_id)
        if not gateway:
            return None
        
        gateway.status = heartbeat.status
        gateway.last_seen = datetime.utcnow()
        if heartbeat.version:
            gateway.version = heartbeat.version
        if heartbeat.metadata:
            gateway.metadata = heartbeat.metadata
        
        self.db.commit()
        self.db.refresh(gateway)
        return gateway
    
    def get_gateway(self, gateway_id: UUID, org_id: UUID) -> Optional[Gateway]:
        """Get a gateway by ID."""
        return self.repo.get(gateway_id, org_id)
    
    def get_gateways(
        self,
        org_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Gateway]:
        """Get all gateways for an organization."""
        return self.repo.get_multi(org_id=org_id, skip=skip, limit=limit)
    
    def get_online_gateways(self, org_id: UUID) -> List[Gateway]:
        """Get all online gateways for an organization."""
        return self.repo.get_online_gateways(org_id)


