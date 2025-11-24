"""Identity Governance Agent (IGA) API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.database import get_db
from app.utils.auth import get_current_user_org_id
from app.models.access_request import AccessRequestStatus, AccessRequestType
from app.services.identity_governance_service import IdentityGovernanceService

router = APIRouter(prefix="/identity-governance", tags=["Identity Governance"])


class AccessRequestCreate(BaseModel):
    requester_id: str = Field(..., description="User ID requesting access")
    resource_id: str = Field(..., description="Resource ID to access")
    resource_type: str = Field(..., description="Type of resource")
    request_type: AccessRequestType = Field(..., description="Type of access request")
    requested_duration_minutes: Optional[int] = Field(None, description="Requested duration in minutes")
    justification: Optional[str] = Field(None, description="Justification for access")


class AccessRequestResponse(BaseModel):
    id: UUID
    request_type: str
    resource_id: str
    resource_type: str
    status: str
    risk_score: Optional[float]
    risk_factors: Optional[dict]
    role_drift_detected: bool
    recommended_scope: Optional[dict]
    requester_id: str
    created_at: str

    class Config:
        from_attributes = True


class AccessRequestEvaluate(BaseModel):
    requester_id: str
    resource_id: str
    resource_type: str
    requested_duration_minutes: Optional[int] = None
    justification: Optional[str] = None


@router.post("/access-requests", response_model=AccessRequestResponse)
async def create_access_request(
    request: AccessRequestCreate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Create a new access request"""
    service = IdentityGovernanceService(db)
    access_request = service.create_access_request(
        org_id=org_id,
        requester_id=request.requester_id,
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        request_type=request.request_type,
        requested_duration_minutes=request.requested_duration_minutes,
        justification=request.justification
    )
    
    return AccessRequestResponse(
        id=access_request.id,
        request_type=access_request.request_type.value,
        resource_id=access_request.resource_id,
        resource_type=access_request.resource_type,
        status=access_request.status.value,
        risk_score=access_request.risk_score,
        risk_factors=access_request.risk_factors,
        role_drift_detected=access_request.role_drift_detected,
        recommended_scope=access_request.recommended_scope,
        requester_id=access_request.requester_id,
        created_at=access_request.created_at.isoformat()
    )


@router.post("/access-requests/evaluate")
async def evaluate_access_request(
    request: AccessRequestEvaluate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Evaluate an access request without creating it"""
    service = IdentityGovernanceService(db)
    evaluation = service.evaluate_access_request(
        org_id=org_id,
        requester_id=request.requester_id,
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        requested_duration_minutes=request.requested_duration_minutes,
        justification=request.justification
    )
    return evaluation


@router.get("/access-requests", response_model=List[AccessRequestResponse])
async def list_access_requests(
    status: Optional[AccessRequestStatus] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """List access requests for the organization"""
    service = IdentityGovernanceService(db)
    requests = service.get_access_requests(org_id=org_id, status=status)
    
    return [
        AccessRequestResponse(
            id=req.id,
            request_type=req.request_type.value,
            resource_id=req.resource_id,
            resource_type=req.resource_type,
            status=req.status.value,
            risk_score=req.risk_score,
            risk_factors=req.risk_factors,
            role_drift_detected=req.role_drift_detected,
            recommended_scope=req.recommended_scope,
            requester_id=req.requester_id,
            created_at=req.created_at.isoformat()
        )
        for req in requests
    ]


@router.post("/access-requests/{request_id}/approve")
async def approve_access_request(
    request_id: UUID,
    approver_id: str,
    approved_duration_minutes: Optional[int] = None,
    rationale: Optional[str] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Approve an access request"""
    service = IdentityGovernanceService(db)
    try:
        access_request = service.approve_access_request(
            request_id=request_id,
            approver_id=approver_id,
            approved_duration_minutes=approved_duration_minutes,
            rationale=rationale
        )
        return {"success": True, "access_request": access_request}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/access-requests/{request_id}/deny")
async def deny_access_request(
    request_id: UUID,
    approver_id: str,
    rationale: Optional[str] = None,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Deny an access request"""
    service = IdentityGovernanceService(db)
    try:
        access_request = service.deny_access_request(
            request_id=request_id,
            approver_id=approver_id,
            rationale=rationale
        )
        return {"success": True, "access_request": access_request}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

