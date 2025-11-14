"""Gateway model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Gateway(BaseModel):
    """Gateway instance model."""
    __tablename__ = "gateways"
    
    name = Column(String(255), nullable=False)
    instance_id = Column(String(255), unique=True, nullable=False, index=True)  # OpAMP instance ID
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    status = Column(String(50), default="unknown", nullable=False)  # 'online', 'offline', 'unknown'
    last_seen = Column(DateTime(timezone=True), nullable=True)
    version = Column(String(50), nullable=True)  # Gateway version
    config_version = Column(Integer, default=0, nullable=False)  # Currently deployed config version
    metadata = Column(JSON, nullable=True)  # Additional gateway metadata
    
    # Relationships
    organization = relationship("Organization", back_populates="gateways")
    deployments = relationship("Deployment", back_populates="gateway")
