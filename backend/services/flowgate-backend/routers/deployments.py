"""Deployment API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from database import get_db
from services.deployment import DeploymentService
from schemas.deployment import DeploymentCreate, DeploymentUpdate, DeploymentResponse

router = APIRouter(prefix="/deployments", tags=["deployments"])

# TODO: Add authentication middleware to extract org_id from JWT
DEFAULT_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    db: Session = Depends(get_db)
):
    """Create a new deployment."""
    service = DeploymentService(db)
    try:
        deployment = service.create_deployment(DEFAULT_ORG_ID, deployment_data)
        return deployment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[DeploymentResponse])
async def list_deployments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all deployments."""
    service = DeploymentService(db)
    deployments = service.get_deployments(DEFAULT_ORG_ID, skip=skip, limit=limit)
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a deployment by ID."""
    service = DeploymentService(db)
    deployment = service.get_deployment(deployment_id, DEFAULT_ORG_ID)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    return deployment


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db)
):
    """Rollback a deployment."""
    service = DeploymentService(db)
    try:
        rollback = service.rollback_deployment(deployment_id, DEFAULT_ORG_ID)
        if not rollback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        return rollback
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


