"""Deployment API router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.deployment_service import DeploymentService
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentStatusUpdate,
)

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    db: Session = Depends(get_db),
):
    """Create a new deployment"""
    service = DeploymentService(db)
    try:
        deployment = service.create_deployment(deployment_data)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DeploymentResponse])
async def list_deployments(
    org_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all deployments for an organization"""
    service = DeploymentService(db)
    deployments = service.get_deployments(org_id, skip, limit)
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a deployment by ID"""
    service = DeploymentService(db)
    deployment = service.get_deployment(deployment_id, org_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.put("/{deployment_id}/status", response_model=DeploymentResponse)
async def update_deployment_status(
    deployment_id: UUID,
    org_id: UUID,
    status_update: DeploymentStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update deployment status"""
    service = DeploymentService(db)
    deployment = service.update_deployment_status(deployment_id, org_id, status_update)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.post("/{deployment_id}/start", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Start a deployment"""
    service = DeploymentService(db)
    deployment = service.start_deployment(deployment_id, org_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.post("/{deployment_id}/complete", response_model=DeploymentResponse)
async def complete_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark deployment as completed"""
    service = DeploymentService(db)
    deployment = service.complete_deployment(deployment_id, org_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.post("/{deployment_id}/fail", response_model=DeploymentResponse)
async def fail_deployment(
    deployment_id: UUID,
    org_id: UUID,
    error_message: str,
    db: Session = Depends(get_db),
):
    """Mark deployment as failed"""
    service = DeploymentService(db)
    deployment = service.fail_deployment(deployment_id, org_id, error_message)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db),
):
    """Rollback a deployment"""
    service = DeploymentService(db)
    deployment = service.rollback_deployment(deployment_id, org_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment

