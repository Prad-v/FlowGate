"""Identity Governance Agent (IGA) Service

Handles access request risk scoring, role drift detection, and entitlement risk analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID
from app.models.access_request import AccessRequest, AccessRequestStatus, AccessRequestType
from app.models.threat_alert import ThreatAlert, ThreatSeverity
from app.core.neo4j_client import get_neo4j_client
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class IdentityGovernanceService:
    """Identity Governance Agent service"""

    def __init__(self, db: Session):
        self.db = db
        self.neo4j_client = get_neo4j_client()
        self.settings_service = SettingsService(db)

    def evaluate_access_request(
        self,
        org_id: UUID,
        requester_id: str,
        resource_id: str,
        resource_type: str,
        requested_duration_minutes: Optional[int] = None,
        justification: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate an access request and return risk score"""
        try:
            # Get user roles from graph
            user_roles = self.neo4j_client.get_user_roles(requester_id)
            
            # Get resource permissions
            resource_permissions = self.neo4j_client.get_resource_permissions(resource_id)
            
            # Find access paths
            access_paths = self.neo4j_client.find_access_paths(requester_id, resource_id)
            
            # Calculate risk score
            risk_score, risk_factors = self._calculate_risk_score(
                requester_id,
                resource_id,
                resource_type,
                user_roles,
                resource_permissions,
                access_paths,
                requested_duration_minutes
            )
            
            # Detect role drift
            role_drift_detected = self._detect_role_drift(requester_id, user_roles)
            
            # Generate recommendations
            recommended_scope = self._generate_recommendations(
                risk_score,
                resource_type,
                requested_duration_minutes
            )
            
            return {
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "role_drift_detected": role_drift_detected,
                "recommended_scope": recommended_scope,
                "access_paths": len(access_paths),
                "user_roles": [r.get("role_name") for r in user_roles]
            }
            
        except Exception as e:
            logger.error(f"Error evaluating access request: {e}")
            return {
                "risk_score": 0.5,  # Default to medium risk on error
                "risk_factors": [f"Error during evaluation: {str(e)}"],
                "role_drift_detected": False,
                "recommended_scope": {},
                "access_paths": 0,
                "user_roles": []
            }

    def create_access_request(
        self,
        org_id: UUID,
        requester_id: str,
        resource_id: str,
        resource_type: str,
        request_type: AccessRequestType,
        requested_duration_minutes: Optional[int] = None,
        justification: Optional[str] = None
    ) -> AccessRequest:
        """Create and evaluate an access request"""
        # Evaluate risk
        evaluation = self.evaluate_access_request(
            org_id,
            requester_id,
            resource_id,
            resource_type,
            requested_duration_minutes,
            justification
        )
        
        # Create access request record
        access_request = AccessRequest(
            organization_id=org_id,
            request_type=request_type,
            resource_id=resource_id,
            resource_type=resource_type,
            justification=justification,
            requested_duration_minutes=requested_duration_minutes,
            requester_id=requester_id,
            risk_score=evaluation["risk_score"],
            risk_factors=evaluation["risk_factors"],
            role_drift_detected=evaluation["role_drift_detected"],
            recommended_scope=evaluation["recommended_scope"],
            status=AccessRequestStatus.PENDING
        )
        
        # Set expiration if duration provided
        if requested_duration_minutes:
            access_request.expires_at = datetime.utcnow() + timedelta(minutes=requested_duration_minutes)
        
        self.db.add(access_request)
        self.db.commit()
        self.db.refresh(access_request)
        
        return access_request

    def _calculate_risk_score(
        self,
        requester_id: str,
        resource_id: str,
        resource_type: str,
        user_roles: List[Dict[str, Any]],
        resource_permissions: List[Dict[str, Any]],
        access_paths: List[Dict[str, Any]],
        requested_duration_minutes: Optional[int]
    ) -> tuple[float, List[str]]:
        """Calculate risk score for access request"""
        risk_score = 0.0
        risk_factors = []
        
        # Factor 1: Number of access paths (more paths = higher risk)
        if len(access_paths) > 3:
            risk_score += 0.2
            risk_factors.append(f"Multiple access paths detected ({len(access_paths)} paths)")
        elif len(access_paths) == 0:
            risk_score += 0.3
            risk_factors.append("No direct access path found - requires privilege escalation")
        
        # Factor 2: Privilege level of roles
        max_privilege = 0
        for role in user_roles:
            privilege = role.get("privilege_level", 0)
            if isinstance(privilege, (int, float)):
                max_privilege = max(max_privilege, privilege)
        
        if max_privilege > 7:  # High privilege
            risk_score += 0.3
            risk_factors.append(f"High privilege role detected (level {max_privilege})")
        
        # Factor 3: Resource type sensitivity
        sensitive_resources = ["database", "admin", "root", "production"]
        if any(sensitive in resource_type.lower() for sensitive in sensitive_resources):
            risk_score += 0.2
            risk_factors.append(f"Sensitive resource type: {resource_type}")
        
        # Factor 4: Requested duration
        if requested_duration_minutes and requested_duration_minutes > 1440:  # > 24 hours
            risk_score += 0.1
            risk_factors.append(f"Long duration requested: {requested_duration_minutes} minutes")
        
        # Factor 5: Recent access patterns (would query from logs)
        # For now, we'll add a baseline risk
        risk_score += 0.1
        
        # Normalize to 0.0-1.0
        risk_score = min(risk_score, 1.0)
        
        if risk_score < 0.3:
            risk_factors.append("Low risk: Standard access pattern")
        elif risk_score < 0.7:
            risk_factors.append("Medium risk: Review recommended")
        else:
            risk_factors.append("High risk: Manual approval required")
        
        return risk_score, risk_factors

    def _detect_role_drift(self, user_id: str, user_roles: List[Dict[str, Any]]) -> bool:
        """Detect if user has role drift (accumulated excessive roles)"""
        # Simple heuristic: if user has more than 5 roles, consider it role drift
        if len(user_roles) > 5:
            return True
        
        # Check for conflicting roles (e.g., both admin and read-only)
        role_names = [r.get("role_name", "").lower() for r in user_roles]
        has_admin = any("admin" in name or "root" in name for name in role_names)
        has_readonly = any("read" in name or "view" in name for name in role_names)
        
        if has_admin and has_readonly:
            return True  # Conflicting roles
        
        return False

    def _generate_recommendations(
        self,
        risk_score: float,
        resource_type: str,
        requested_duration_minutes: Optional[int]
    ) -> Dict[str, Any]:
        """Generate recommendations based on risk score"""
        recommendations = {
            "auto_approve": risk_score < 0.3,
            "require_approval": risk_score >= 0.3,
            "limit_duration": None,
            "restrict_scope": None
        }
        
        # Recommend duration limits for high-risk requests
        if risk_score >= 0.7:
            recommendations["limit_duration"] = min(requested_duration_minutes or 60, 60)  # Max 1 hour
            recommendations["restrict_scope"] = "read_only"  # Restrict to read-only
        
        elif risk_score >= 0.5:
            recommendations["limit_duration"] = min(requested_duration_minutes or 240, 240)  # Max 4 hours
        
        return recommendations

    def get_access_requests(
        self,
        org_id: UUID,
        status: Optional[AccessRequestStatus] = None,
        limit: int = 100
    ) -> List[AccessRequest]:
        """Get access requests for an organization"""
        query = self.db.query(AccessRequest).filter(
            AccessRequest.organization_id == org_id
        )
        
        if status:
            query = query.filter(AccessRequest.status == status)
        
        return query.order_by(AccessRequest.created_at.desc()).limit(limit).all()

    def approve_access_request(
        self,
        request_id: UUID,
        approver_id: str,
        approved_duration_minutes: Optional[int] = None,
        rationale: Optional[str] = None
    ) -> AccessRequest:
        """Approve an access request"""
        access_request = self.db.query(AccessRequest).filter(
            AccessRequest.id == request_id
        ).first()
        
        if not access_request:
            raise ValueError(f"Access request not found: {request_id}")
        
        access_request.status = AccessRequestStatus.APPROVED
        access_request.approver_id = approver_id
        access_request.approved_at = datetime.utcnow()
        access_request.approval_rationale = rationale
        
        if approved_duration_minutes:
            access_request.approved_duration_minutes = approved_duration_minutes
            access_request.expires_at = datetime.utcnow() + timedelta(minutes=approved_duration_minutes)
        
        # Generate access token (simplified - in production, use proper token generation)
        access_request.access_token = f"token_{request_id}_{datetime.utcnow().timestamp()}"
        access_request.access_granted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(access_request)
        
        return access_request

    def deny_access_request(
        self,
        request_id: UUID,
        approver_id: str,
        rationale: Optional[str] = None
    ) -> AccessRequest:
        """Deny an access request"""
        access_request = self.db.query(AccessRequest).filter(
            AccessRequest.id == request_id
        ).first()
        
        if not access_request:
            raise ValueError(f"Access request not found: {request_id}")
        
        access_request.status = AccessRequestStatus.DENIED
        access_request.approver_id = approver_id
        access_request.approved_at = datetime.utcnow()
        access_request.approval_rationale = rationale or "Access denied"
        
        self.db.commit()
        self.db.refresh(access_request)
        
        return access_request

