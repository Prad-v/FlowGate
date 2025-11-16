"""Package Management API router for OpAMP package management"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.package_service import PackageService
from app.services.gateway_service import GatewayService
from app.schemas.package import (
    PackageCreate, PackageUpdate, PackageResponse, PackageStatusUpdate
)
from app.utils.auth import get_current_user_org_id
from app.models.agent_package import PackageType

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("/gateways/{gateway_id}", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package_offer(
    gateway_id: UUID,
    package_data: PackageCreate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Create a package offer for a gateway"""
    # Verify gateway belongs to org
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_id(gateway_id)
    
    if not gateway or gateway.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    # Create package offer
    package_service = PackageService(db)
    
    # Convert signature from hex string to bytes if provided
    signature_bytes = None
    if package_data.signature:
        try:
            signature_bytes = bytes.fromhex(package_data.signature)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature format (must be hex-encoded)"
            )
    
    package = package_service.create_package_offer(
        gateway_id=gateway_id,
        org_id=org_id,
        package_name=package_data.package_name,
        package_version=package_data.package_version,
        package_type=package_data.package_type,
        download_url=package_data.download_url,
        content_hash=package_data.content_hash,
        signature=signature_bytes,
    )
    
    return package


@router.get("/gateways/{gateway_id}", response_model=List[PackageResponse])
async def get_packages_for_gateway(
    gateway_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get all packages for a gateway"""
    # Verify gateway belongs to org
    gateway_service = GatewayService(db)
    gateway = gateway_service.repository.get_by_id(gateway_id)
    
    if not gateway or gateway.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    package_service = PackageService(db)
    packages = package_service.get_packages_for_gateway(gateway_id, org_id)
    
    return packages


@router.get("/{package_id}", response_model=PackageResponse)
async def get_package(
    package_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Get a package by ID"""
    package_service = PackageService(db)
    package = package_service.get_package(package_id, org_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return package


@router.put("/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: UUID,
    package_data: PackageUpdate,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Update a package offer"""
    package_service = PackageService(db)
    package = package_service.get_package(package_id, org_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Update package fields
    if package_data.package_version is not None:
        package.package_version = package_data.package_version
    if package_data.download_url is not None:
        package.download_url = package_data.download_url
    if package_data.content_hash is not None:
        package.content_hash = package_data.content_hash
    if package_data.signature is not None:
        try:
            package.signature = bytes.fromhex(package_data.signature)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature format (must be hex-encoded)"
            )
    
    # Recalculate package hash
    package.package_hash = package_service._calculate_package_hash(
        package.package_name,
        package.package_version or "",
        package.download_url,
        package.content_hash
    )
    
    db.commit()
    db.refresh(package)
    
    return package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: UUID,
    org_id: UUID = Depends(get_current_user_org_id),
    db: Session = Depends(get_db),
):
    """Delete a package offer"""
    package_service = PackageService(db)
    package = package_service.get_package(package_id, org_id)
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    db.delete(package)
    db.commit()
    
    return None

