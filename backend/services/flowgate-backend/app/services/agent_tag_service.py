"""Agent Tagging Service

Service for managing tags on agents (gateways) for selective config rollouts.
"""

from typing import List, Optional, Set
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.agent_tag import AgentTag
from app.models.gateway import Gateway


class AgentTagService:
    """Service for managing agent tags"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_tag_to_agent(self, gateway_id: UUID, tag: str, created_by: Optional[UUID] = None) -> AgentTag:
        """
        Add a tag to an agent
        
        Args:
            gateway_id: Gateway UUID
            tag: Tag name (will be normalized to lowercase)
            created_by: User UUID who created the tag
            
        Returns:
            AgentTag object
        """
        # Normalize tag (lowercase, trim)
        tag = tag.strip().lower()
        
        # Check if tag already exists
        existing = self.db.query(AgentTag).filter(
            and_(
                AgentTag.gateway_id == gateway_id,
                AgentTag.tag == tag
            )
        ).first()
        
        if existing:
            return existing
        
        # Create new tag
        agent_tag = AgentTag(
            gateway_id=gateway_id,
            tag=tag,
            created_by=created_by
        )
        self.db.add(agent_tag)
        
        # Update gateway's tags JSONB field for quick filtering
        gateway = self.db.query(Gateway).filter(Gateway.id == gateway_id).first()
        if gateway:
            current_tags = gateway.tags or []
            if tag not in current_tags:
                current_tags.append(tag)
                gateway.tags = current_tags
        
        self.db.commit()
        self.db.refresh(agent_tag)
        return agent_tag
    
    def remove_tag_from_agent(self, gateway_id: UUID, tag: str) -> bool:
        """
        Remove a tag from an agent
        
        Args:
            gateway_id: Gateway UUID
            tag: Tag name (will be normalized)
            
        Returns:
            True if tag was removed, False if it didn't exist
        """
        tag = tag.strip().lower()
        
        agent_tag = self.db.query(AgentTag).filter(
            and_(
                AgentTag.gateway_id == gateway_id,
                AgentTag.tag == tag
            )
        ).first()
        
        if not agent_tag:
            return False
        
        self.db.delete(agent_tag)
        
        # Update gateway's tags JSONB field
        gateway = self.db.query(Gateway).filter(Gateway.id == gateway_id).first()
        if gateway and gateway.tags:
            current_tags = gateway.tags
            if tag in current_tags:
                current_tags.remove(tag)
                gateway.tags = current_tags if current_tags else None
        
        self.db.commit()
        return True
    
    def get_agent_tags(self, gateway_id: UUID) -> List[str]:
        """
        Get all tags for an agent
        
        Args:
            gateway_id: Gateway UUID
            
        Returns:
            List of tag names
        """
        tags = self.db.query(AgentTag).filter(
            AgentTag.gateway_id == gateway_id
        ).all()
        return [tag.tag for tag in tags]
    
    def get_agents_by_tags(
        self, 
        org_id: UUID, 
        tags: Optional[List[str]] = None,
        require_all: bool = False
    ) -> List[Gateway]:
        """
        Get agents matching tag criteria
        
        Args:
            org_id: Organization UUID
            tags: List of tag names to filter by (None = all agents)
            require_all: If True, agent must have all tags. If False, agent must have any tag.
            
        Returns:
            List of Gateway objects
        """
        query = self.db.query(Gateway).filter(Gateway.org_id == org_id)
        
        if not tags:
            # Return all agents in org
            return query.all()
        
        # Normalize tags
        tags = [t.strip().lower() for t in tags]
        
        if require_all:
            # Agent must have all tags
            # Use JSONB contains for each tag
            for tag in tags:
                query = query.filter(Gateway.tags.contains([tag]))
        else:
            # Agent must have any tag
            # Use JSONB overlap
            query = query.filter(Gateway.tags.overlap(tags))
        
        return query.all()
    
    def get_all_tags(self, org_id: UUID) -> List[dict]:
        """
        Get all unique tags for an organization with counts
        
        Args:
            org_id: Organization UUID
            
        Returns:
            List of dicts with 'tag' and 'count' keys
        """
        # Get all gateways in org
        gateways = self.db.query(Gateway).filter(Gateway.org_id == org_id).all()
        
        # Collect all tags with counts
        tag_counts = {}
        for gateway in gateways:
            if gateway.tags:
                for tag in gateway.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Convert to list of dicts
        return [
            {"tag": tag, "count": count}
            for tag, count in sorted(tag_counts.items())
        ]
    
    def bulk_tag_agents(
        self, 
        gateway_ids: List[UUID], 
        tags: List[str],
        created_by: Optional[UUID] = None
    ) -> int:
        """
        Tag multiple agents at once
        
        Args:
            gateway_ids: List of gateway UUIDs
            tags: List of tag names to add
            created_by: User UUID who created the tags
            
        Returns:
            Number of tags added
        """
        count = 0
        for gateway_id in gateway_ids:
            for tag in tags:
                try:
                    self.add_tag_to_agent(gateway_id, tag, created_by)
                    count += 1
                except Exception:
                    # Skip duplicates or errors
                    pass
        return count
    
    def bulk_remove_tags(
        self,
        gateway_ids: List[UUID],
        tags: List[str]
    ) -> int:
        """
        Remove tags from multiple agents
        
        Args:
            gateway_ids: List of gateway UUIDs
            tags: List of tag names to remove
            
        Returns:
            Number of tags removed
        """
        count = 0
        for gateway_id in gateway_ids:
            for tag in tags:
                if self.remove_tag_from_agent(gateway_id, tag):
                    count += 1
        return count

