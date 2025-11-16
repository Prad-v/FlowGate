"""Package Service for OpAMP package management"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.agent_package import AgentPackage, PackageStatus, PackageType
from app.models.gateway import Gateway
import hashlib
import logging

logger = logging.getLogger(__name__)


class PackageService:
    """Service for managing agent packages via OpAMP"""

    def __init__(self, db: Session):
        self.db = db

    def get_packages_for_gateway(
        self, gateway_id: UUID, org_id: UUID
    ) -> List[AgentPackage]:
        """Get all packages for a gateway"""
        return self.db.query(AgentPackage).filter(
            and_(
                AgentPackage.gateway_id == gateway_id,
                AgentPackage.org_id == org_id
            )
        ).all()

    def get_package(
        self, package_id: UUID, org_id: UUID
    ) -> Optional[AgentPackage]:
        """Get a package by ID"""
        return self.db.query(AgentPackage).filter(
            and_(
                AgentPackage.id == package_id,
                AgentPackage.org_id == org_id
            )
        ).first()

    def create_package_offer(
        self,
        gateway_id: UUID,
        org_id: UUID,
        package_name: str,
        package_version: str,
        package_type: PackageType,
        download_url: str,
        content_hash: Optional[str] = None,
        signature: Optional[bytes] = None,
    ) -> AgentPackage:
        """Create a package offer for a gateway"""
        # Check if package already exists
        existing = self.db.query(AgentPackage).filter(
            and_(
                AgentPackage.gateway_id == gateway_id,
                AgentPackage.package_name == package_name,
                AgentPackage.org_id == org_id
            )
        ).first()

        if existing:
            # Update existing package offer
            existing.package_version = package_version
            existing.package_type = package_type
            existing.download_url = download_url
            existing.content_hash = content_hash
            existing.signature = signature
            existing.status = PackageStatus.UNINSTALLED  # Reset to uninstalled when new version offered
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Calculate package hash (simplified - in production, use proper hash calculation)
        package_hash = self._calculate_package_hash(
            package_name, package_version, download_url, content_hash
        )

        package = AgentPackage(
            gateway_id=gateway_id,
            org_id=org_id,
            package_name=package_name,
            package_version=package_version,
            package_type=package_type,
            download_url=download_url,
            content_hash=content_hash,
            signature=signature,
            package_hash=package_hash,
            server_offered_hash=package_hash,
            status=PackageStatus.UNINSTALLED,
        )
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return package

    def update_package_status(
        self,
        gateway_id: UUID,
        package_name: str,
        status: PackageStatus,
        agent_reported_hash: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AgentPackage]:
        """Update package status from agent report"""
        package = self.db.query(AgentPackage).filter(
            and_(
                AgentPackage.gateway_id == gateway_id,
                AgentPackage.package_name == package_name
            )
        ).first()

        if not package:
            logger.warning(f"Package {package_name} not found for gateway {gateway_id}")
            return None

        package.status = status
        if agent_reported_hash:
            package.agent_reported_hash = agent_reported_hash
        if error_message:
            package.error_message = error_message
        if status == PackageStatus.INSTALLED:
            package.installed_at = datetime.utcnow()
        elif status == PackageStatus.FAILED:
            package.error_message = error_message or "Installation failed"

        package.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(package)
        return package

    def get_packages_available_for_gateway(
        self, gateway_id: UUID, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get packages that should be offered to a gateway"""
        # Use enum values (lowercase strings) that match the database enum
        packages = self.db.query(AgentPackage).filter(
            and_(
                AgentPackage.gateway_id == gateway_id,
                AgentPackage.org_id == org_id,
                AgentPackage.status.in_([
                    "uninstalled",  # Use string literal matching database enum value
                    "failed"        # Use string literal matching database enum value
                ])
            )
        ).all()

        result = []
        for package in packages:
            result.append({
                "package_name": package.package_name,
                "package_version": package.package_version,
                "package_type": package.package_type.value,
                "download_url": package.download_url,
                "content_hash": package.content_hash,
                "signature": package.signature.hex() if package.signature else None,
                "package_hash": package.package_hash,
            })
        return result

    def _calculate_package_hash(
        self,
        package_name: str,
        package_version: str,
        download_url: str,
        content_hash: Optional[str] = None,
    ) -> str:
        """Calculate hash for package identification"""
        # Combine package info for hash
        hash_input = f"{package_name}:{package_version}:{download_url}"
        if content_hash:
            hash_input += f":{content_hash}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def verify_package_signature(
        self, package_content: bytes, signature: bytes
    ) -> bool:
        """Verify package signature (placeholder - implement proper verification)"""
        # TODO: Implement proper signature verification
        # This should verify GPG signature or other signing mechanism
        logger.warning("Package signature verification not yet implemented")
        return True  # Placeholder

