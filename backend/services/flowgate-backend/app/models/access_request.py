"""Access Request model for Identity Governance Agent (IGA)"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base
from app.models.base import BaseModel


class AccessRequestStatus(str, enum.Enum):
    """Access request status"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AccessRequestType(str, enum.Enum):
    """Type of access request"""
    JITA = "jita"  # Just-In-Time Access
    JITP = "jitp"  # Just-In-Time Privilege
    STANDARD = "standard"


class AccessRequest(Base, BaseModel):
    """Access request for JITA/JITP"""

    __tablename__ = "access_requests"

    # Request information
    request_type = Column(
        SQLEnum(AccessRequestType, name="access_request_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    resource_id = Column(String(255), nullable=False, index=True)  # Resource being accessed
    resource_type = Column(String(100), nullable=False)  # server, database, api, etc.
    justification = Column(Text, nullable=True)
    
    # Duration
    requested_duration_minutes = Column(Integer, nullable=True)  # Requested duration
    approved_duration_minutes = Column(Integer, nullable=True)  # Approved duration (may be limited)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Requester information
    requester_id = Column(String(255), nullable=False, index=True)  # User ID
    requester_email = Column(String(255), nullable=True)
    requester_name = Column(String(255), nullable=True)

    # Risk assessment (from IGA)
    risk_score = Column(Float, nullable=True)  # 0.0 to 1.0
    risk_factors = Column(postgresql.JSONB, nullable=True)  # List of risk factors
    recommended_scope = Column(postgresql.JSONB, nullable=True)  # IGA recommendations
    role_drift_detected = Column(Boolean, default=False, nullable=False)

    # Approval workflow
    status = Column(
        SQLEnum(AccessRequestStatus, name="access_request_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AccessRequestStatus.PENDING,
        index=True
    )
    approver_id = Column(String(255), nullable=True)  # User ID of approver
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_rationale = Column(Text, nullable=True)

    # Access details (if approved)
    access_token = Column(String(512), nullable=True)  # Token/session ID if issued
    access_granted_at = Column(DateTime(timezone=True), nullable=True)
    access_revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization_id = Column(postgresql.UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="access_requests")

