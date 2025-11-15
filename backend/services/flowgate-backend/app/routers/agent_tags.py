"""Agent Tagging API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.services.agent_tag_service import AgentTagService
from app.schemas.opamp_config import (
    AgentTagRequest,
    AgentTagResponse,
    TagInfo,
    BulkTagRequest,
    BulkRemoveTagRequest
)

router = APIRouter(prefix="/agents", tags=["agent-tags"])


@router.post("/{gateway_id}/tags", response_model=AgentTagResponse, status_code=status.HTTP_201_CREATED)
async def add_tag_to_agent(
    gateway_id: UUID,
    tag_data: AgentTagRequest,
    org_id: UUID,
    db: Session = Depends(get_db),
    # TODO: Add authentication
    # current_user: User = Depends(get_current_user)
):
    """Add tag to agent"""
    # Verify gateway belongs to org
    from app.models.gateway import Gateway
    
    gateway = db.query(Gateway).filter(
        Gateway.id == gateway_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    service = AgentTagService(db)
    agent_tag = service.add_tag_to_agent(
        gateway_id=gateway_id,
        tag=tag_data.tag,
        created_by=None  # TODO: Get from current_user
    )
    
    return agent_tag


@router.delete("/{gateway_id}/tags/{tag}")
async def remove_tag_from_agent(
    gateway_id: UUID,
    tag: str,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove tag from agent"""
    # Verify gateway belongs to org
    from app.models.gateway import Gateway
    
    gateway = db.query(Gateway).filter(
        Gateway.id == gateway_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    service = AgentTagService(db)
    removed = service.remove_tag_from_agent(gateway_id, tag)
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return {"message": "Tag removed successfully"}


@router.get("/{gateway_id}/tags", response_model=List[str])
async def get_agent_tags(
    gateway_id: UUID,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get tags for an agent"""
    # Verify gateway belongs to org
    from app.models.gateway import Gateway
    
    gateway = db.query(Gateway).filter(
        Gateway.id == gateway_id,
        Gateway.org_id == org_id
    ).first()
    
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gateway not found"
        )
    
    service = AgentTagService(db)
    tags = service.get_agent_tags(gateway_id)
    return tags


@router.get("/tags", response_model=List[TagInfo])
async def get_all_tags(
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all tags for an organization with counts"""
    service = AgentTagService(db)
    tags = service.get_all_tags(org_id)
    return tags


@router.post("/tags/bulk")
async def bulk_tag_agents(
    bulk_data: BulkTagRequest,
    org_id: UUID,
    db: Session = Depends(get_db),
    # TODO: Add authentication
    # current_user: User = Depends(get_current_user)
):
    """Bulk tag multiple agents"""
    # Verify all gateways belong to org
    from app.models.gateway import Gateway
    
    gateways = db.query(Gateway).filter(
        Gateway.id.in_(bulk_data.gateway_ids),
        Gateway.org_id == org_id
    ).all()
    
    if len(gateways) != len(bulk_data.gateway_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some gateways not found or don't belong to organization"
        )
    
    service = AgentTagService(db)
    count = service.bulk_tag_agents(
        gateway_ids=bulk_data.gateway_ids,
        tags=bulk_data.tags,
        created_by=None  # TODO: Get from current_user
    )
    
    return {"message": f"Added {count} tags"}


@router.post("/tags/bulk-remove")
async def bulk_remove_tags(
    bulk_data: BulkRemoveTagRequest,
    org_id: UUID,
    db: Session = Depends(get_db)
):
    """Bulk remove tags from multiple agents"""
    # Verify all gateways belong to org
    from app.models.gateway import Gateway
    
    gateways = db.query(Gateway).filter(
        Gateway.id.in_(bulk_data.gateway_ids),
        Gateway.org_id == org_id
    ).all()
    
    if len(gateways) != len(bulk_data.gateway_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some gateways not found or don't belong to organization"
        )
    
    service = AgentTagService(db)
    count = service.bulk_remove_tags(
        gateway_ids=bulk_data.gateway_ids,
        tags=bulk_data.tags
    )
    
    return {"message": f"Removed {count} tags"}

