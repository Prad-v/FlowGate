"""Persona Baseline Agent (PBA) Service

Handles user/service behavior baseline learning and anomaly detection.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.models.persona_baseline import PersonaBaseline, PersonaAnomaly, EntityType

logger = logging.getLogger(__name__)


class PersonaBaselineService:
    """Persona Baseline Agent service"""

    def __init__(self, db: Session):
        self.db = db

    def update_baseline(
        self,
        org_id: UUID,
        entity_type: EntityType,
        entity_id: str,
        event_data: Dict[str, Any]
    ) -> PersonaBaseline:
        """Update behavior baseline for an entity"""
        # Get or create baseline
        baseline = self.db.query(PersonaBaseline).filter(
            PersonaBaseline.organization_id == org_id,
            PersonaBaseline.entity_type == entity_type,
            PersonaBaseline.entity_id == entity_id
        ).first()
        
        if not baseline:
            baseline = PersonaBaseline(
                organization_id=org_id,
                entity_type=entity_type,
                entity_id=entity_id,
                sample_count=0,
                is_active=True
            )
            self.db.add(baseline)
        
        # Update baseline stats
        baseline.sample_count += 1
        baseline.last_updated_at = datetime.utcnow()
        
        # Simple baseline update (in production, use ML/embeddings)
        if not baseline.baseline_stats:
            baseline.baseline_stats = {}
        
        # Update behavior patterns
        if not baseline.behavior_patterns:
            baseline.behavior_patterns = []
        
        self.db.commit()
        self.db.refresh(baseline)
        
        return baseline

    def detect_anomaly(
        self,
        org_id: UUID,
        entity_type: EntityType,
        entity_id: str,
        event_data: Dict[str, Any],
        event_timestamp: datetime
    ) -> Optional[PersonaAnomaly]:
        """Detect anomaly in entity behavior"""
        # Get baseline
        baseline = self.db.query(PersonaBaseline).filter(
            PersonaBaseline.organization_id == org_id,
            PersonaBaseline.entity_type == entity_type,
            PersonaBaseline.entity_id == entity_id,
            PersonaBaseline.is_active == True
        ).first()
        
        if not baseline or baseline.sample_count < 10:
            # Not enough data for anomaly detection
            return None
        
        # Calculate deviation score (simplified)
        deviation_score = self._calculate_deviation_score(baseline, event_data)
        
        if deviation_score > baseline.anomaly_threshold:
            # Create anomaly record
            anomaly = PersonaAnomaly(
                baseline_id=baseline.id,
                deviation_score=deviation_score,
                anomaly_type="behavior_deviation",
                event_data=event_data,
                event_timestamp=event_timestamp
            )
            
            self.db.add(anomaly)
            self.db.commit()
            self.db.refresh(anomaly)
            
            return anomaly
        
        return None

    def _calculate_deviation_score(
        self,
        baseline: PersonaBaseline,
        event_data: Dict[str, Any]
    ) -> float:
        """Calculate deviation score from baseline"""
        # Simplified deviation calculation
        # In production, use embeddings and cosine similarity
        score = 0.0
        
        # Check for unusual patterns
        if baseline.baseline_stats:
            # Compare event data with baseline
            # This is a placeholder - real implementation would use ML
            score = 0.5  # Default moderate deviation
        
        return score

    def get_baselines(
        self,
        org_id: UUID,
        entity_type: Optional[EntityType] = None,
        limit: int = 100
    ) -> List[PersonaBaseline]:
        """Get persona baselines for an organization"""
        query = self.db.query(PersonaBaseline).filter(
            PersonaBaseline.organization_id == org_id
        )
        
        if entity_type:
            query = query.filter(PersonaBaseline.entity_type == entity_type)
        
        return query.order_by(PersonaBaseline.last_updated_at.desc()).limit(limit).all()

