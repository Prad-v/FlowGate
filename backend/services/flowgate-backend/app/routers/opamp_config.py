"""OpAMP Config Management API Router"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.opamp_config_service import OpAMPConfigService
from app.models.gateway import OpAMPRemoteConfigStatus
from app.schemas.opamp_config import (
    OpAMPConfigDeploymentCreate,
    OpAMPConfigDeploymentResponse,
    OpAMPConfigPushRequest,
    ConfigDeploymentStatus,
    ConfigAuditEntry,
    AgentConfigHistoryEntry,
    ConfigValidationResult
)

router = APIRouter(prefix="/opamp-config", tags=["opamp-config"])


@router.post("/deployments", response_model=OpAMPConfigDeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_config_deployment(
    deployment_data: OpAMPConfigDeploymentCreate,
    org_id: UUID,
    db: Session = Depends(get_db),
    # TODO: Add authentication to get current user
    # current_user: User = Depends(get_current_user)
):
    """Create new OpAMP config deployment"""
    service = OpAMPConfigService(db)
    
    try:
        deployment, validation_result = service.create_config_deployment(
            name=deployment_data.name,
            config_yaml=deployment_data.config_yaml,
            org_id=org_id,
            rollout_strategy=deployment_data.rollout_strategy,
            canary_percentage=deployment_data.canary_percentage,
            target_tags=deployment_data.target_tags,
            ignore_failures=deployment_data.ignore_failures,
            template_id=deployment_data.template_id,
            template_version=deployment_data.template_version,
            created_by=None  # TODO: Get from current_user
        )
        
        # Push config to agents if immediate rollout
        if deployment_data.rollout_strategy == "immediate":
            service.push_config_to_agents(deployment.id, org_id)
        elif deployment_data.rollout_strategy == "canary":
            service.execute_canary_rollout(deployment.id, org_id)
        
        return deployment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/deployments", response_model=List[OpAMPConfigDeploymentResponse])
async def list_config_deployments(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """List all config deployments for an organization"""
    from app.models.opamp_config_deployment import OpAMPConfigDeployment
    
    deployments = db.query(OpAMPConfigDeployment).filter(
        OpAMPConfigDeployment.org_id == org_id
    ).order_by(OpAMPConfigDeployment.created_at.desc()).all()
    
    return deployments


@router.get("/deployments/{deployment_id}", response_model=OpAMPConfigDeploymentResponse)
async def get_config_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get config deployment details"""
    from app.models.opamp_config_deployment import OpAMPConfigDeployment
    
    deployment = db.query(OpAMPConfigDeployment).filter(
        OpAMPConfigDeployment.id == deployment_id,
        OpAMPConfigDeployment.org_id == org_id
    ).first()
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    return deployment


@router.get("/deployments/{deployment_id}/status", response_model=ConfigDeploymentStatus)
async def get_deployment_status(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get deployment status across all agents"""
    service = OpAMPConfigService(db)
    
    try:
        status_data = service.get_config_deployment_status(deployment_id, org_id)
        return status_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/deployments/{deployment_id}/audit", response_model=List[ConfigAuditEntry])
async def get_deployment_audit(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get audit log for a deployment"""
    service = OpAMPConfigService(db)
    
    try:
        audit_log = service.get_deployment_audit_log(deployment_id, org_id)
        return audit_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/deployments/{deployment_id}/rollback", response_model=OpAMPConfigDeploymentResponse)
async def rollback_deployment(
    deployment_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Rollback a failed deployment"""
    service = OpAMPConfigService(db)
    
    try:
        deployment = service.rollback_config_deployment(deployment_id, org_id)
        return deployment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/push")
async def push_config_direct(
    push_data: OpAMPConfigPushRequest,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Direct push config to agents (bypass deployment)"""
    service = OpAMPConfigService(db)
    
    # Validate config
    validation_result = service.validate_config_yaml(push_data.config_yaml)
    if not validation_result.is_valid and not push_data.ignore_failures:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration validation failed: {', '.join(service.validator.get_validation_errors(validation_result))}"
        )
    
    # Create a temporary deployment for direct push
    deployment, _ = service.create_config_deployment(
        name=f"Direct Push - {datetime.utcnow().isoformat()}",
        config_yaml=push_data.config_yaml,
        org_id=org_id,
        rollout_strategy="immediate",
        target_tags=push_data.target_tags,
        ignore_failures=push_data.ignore_failures
    )
    
    # Push to specific agents if provided
    if push_data.gateway_ids:
        # Filter to only push to specified gateways
        from app.models.opamp_config_audit import OpAMPConfigAudit, OpAMPConfigAuditStatus
        from app.models.gateway import Gateway
        
        # Delete existing audit entries for this deployment
        db.query(OpAMPConfigAudit).filter(
            OpAMPConfigAudit.deployment_id == deployment.id
        ).delete()
        
        # Create audit entries only for specified gateways
        for gateway_id in push_data.gateway_ids:
            gateway = db.query(Gateway).filter(
                Gateway.id == gateway_id,
                Gateway.org_id == org_id
            ).first()
            if gateway:
                audit_entry = OpAMPConfigAudit(
                    deployment_id=deployment.id,
                    gateway_id=gateway_id,
                    config_version=deployment.config_version,
                    config_hash=deployment.config_hash,
                    status=OpAMPConfigAuditStatus.PENDING
                )
                db.add(audit_entry)
                
                # Update gateway to indicate pending config
                gateway.last_config_deployment_id = deployment.id
                gateway.last_config_version = deployment.config_version
                gateway.last_config_status = OpAMPRemoteConfigStatus.UNSET
                gateway.last_config_status_at = datetime.utcnow()
        
        db.commit()
        return {
            "deployment_id": str(deployment.id),
            "target_agents_count": len(push_data.gateway_ids),
            "config_version": deployment.config_version,
            "status": "pushed"
        }
    
    # Push config to all agents matching tags
    result = service.push_config_to_agents(deployment.id, org_id)
    return result


@router.get("/current")
async def get_current_config(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get current config from gateway (for default template)"""
    from app.services.gateway_service import GatewayService
    
    gateway_service = GatewayService(db)
    config = gateway_service.get_agent_config(gateway_id, org_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active config found for this gateway"
        )
    
    return config


@router.post("/validate", response_model=ConfigValidationResult)
async def validate_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """Validate YAML configuration"""
    # Read YAML from request body
    config_yaml = await request.body()
    config_yaml_str = config_yaml.decode('utf-8')
    
    service = OpAMPConfigService(db)
    result = service.validate_config_yaml(config_yaml_str)
    
    # Convert ValidationError to schema
    from app.schemas.opamp_config import ValidationErrorSchema
    
    errors = [
        ValidationErrorSchema(
            level=e.level,
            message=e.message,
            field=e.field,
            line=e.line
        )
        for e in result.errors
    ]
    
    warnings = [
        ValidationErrorSchema(
            level=w.level,
            message=w.message,
            field=w.field,
            line=w.line
        )
        for w in result.warnings
    ]
    
    return ConfigValidationResult(
        is_valid=result.is_valid,
        errors=errors,
        warnings=warnings
    )

