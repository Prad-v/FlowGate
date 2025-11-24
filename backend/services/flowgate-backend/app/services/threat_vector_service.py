"""Threat Vector Agent (TVA) Service

Handles MITRE ATT&CK TTP mapping, anomaly detection, and threat alert generation.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.models.threat_alert import ThreatAlert, ThreatSeverity, ThreatStatus
from app.services.threat_intel_service import ThreatIntelService

logger = logging.getLogger(__name__)


class ThreatVectorService:
    """Threat Vector Agent service"""

    def __init__(self, db: Session):
        self.db = db
        self.threat_intel_service = ThreatIntelService(db)

    async def analyze_log(
        self,
        org_id: str,
        source_type: str,
        log_data: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ThreatAlert]:
        """Analyze a log entry for threats and create alert if detected"""
        try:
            # Get MITRE TTP mappings
            ttp_matches = await self._match_mitre_ttps(log_data, source_type)
            
            # Calculate anomaly score
            anomaly_score = self._calculate_anomaly_score(log_data, source_type, metadata)
            
            # Determine if threat is detected
            if ttp_matches or anomaly_score > 0.7:
                # Create threat alert
                alert = self._create_threat_alert(
                    org_id=org_id,
                    source_type=source_type,
                    log_data=log_data,
                    ttp_matches=ttp_matches,
                    anomaly_score=anomaly_score,
                    metadata=metadata
                )
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing log for threats: {e}")
            return None

    async def _match_mitre_ttps(
        self,
        log_data: str,
        source_type: str
    ) -> List[Dict[str, Any]]:
        """Match log patterns to MITRE ATT&CK TTPs"""
        ttp_matches = []
        
        # Get MITRE framework data
        mitre_data = self.threat_intel_service.get_mitre_framework()
        
        # Simple pattern matching (in production, use ML/embeddings)
        log_lower = log_data.lower()
        
        # Check for common attack patterns
        attack_patterns = {
            "T1055": {"name": "Process Injection", "patterns": ["inject", "dll", "process hollow"]},
            "T1078": {"name": "Valid Accounts", "patterns": ["unauthorized access", "failed login", "brute force"]},
            "T1083": {"name": "File and Directory Discovery", "patterns": ["dir", "ls", "find", "tree"]},
            "T1105": {"name": "Ingress Tool Transfer", "patterns": ["download", "wget", "curl", "powershell download"]},
        }
        
        for technique_id, technique_data in attack_patterns.items():
            for pattern in technique_data["patterns"]:
                if pattern in log_lower:
                    ttp_matches.append({
                        "technique_id": technique_id,
                        "technique_name": technique_data["name"],
                        "confidence": 0.7,
                        "matched_pattern": pattern
                    })
                    break  # Only match once per technique
        
        return ttp_matches

    def _calculate_anomaly_score(
        self,
        log_data: str,
        source_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate anomaly score for log entry"""
        score = 0.0
        
        # Factor 1: Unusual keywords
        suspicious_keywords = ["exploit", "malware", "backdoor", "trojan", "ransomware", "phishing"]
        log_lower = log_data.lower()
        for keyword in suspicious_keywords:
            if keyword in log_lower:
                score += 0.2
        
        # Factor 2: Unusual source
        if source_type not in ["identity", "network", "endpoint", "application"]:
            score += 0.1
        
        # Factor 3: Metadata anomalies
        if metadata:
            if metadata.get("error_count", 0) > 10:
                score += 0.2
            if metadata.get("unusual_time", False):
                score += 0.1
        
        return min(score, 1.0)

    def _create_threat_alert(
        self,
        org_id: str,
        source_type: str,
        log_data: str,
        ttp_matches: List[Dict[str, Any]],
        anomaly_score: float,
        metadata: Optional[Dict[str, Any]]
    ) -> ThreatAlert:
        """Create a threat alert from analysis"""
        # Determine severity
        if ttp_matches:
            severity = ThreatSeverity.HIGH
        elif anomaly_score > 0.8:
            severity = ThreatSeverity.HIGH
        elif anomaly_score > 0.6:
            severity = ThreatSeverity.MEDIUM
        else:
            severity = ThreatSeverity.LOW
        
        # Extract MITRE technique info
        mitre_technique_id = ttp_matches[0]["technique_id"] if ttp_matches else None
        mitre_technique_name = ttp_matches[0]["technique_name"] if ttp_matches else None
        
        # Create alert
        alert = ThreatAlert(
            organization_id=UUID(org_id),
            title=f"Threat Detected: {mitre_technique_name or 'Anomaly Detected'}",
            description=f"Threat detected in {source_type} logs",
            severity=severity,
            status=ThreatStatus.NEW,
            mitre_technique_id=mitre_technique_id,
            mitre_technique_name=mitre_technique_name,
            source_type=source_type,
            source_entity=metadata.get("entity_id") if metadata else None,
            confidence_score=anomaly_score,
            anomaly_score=anomaly_score,
            detection_method="ml_based" if anomaly_score > 0.7 else "rule_based",
            raw_log_data={"log": log_data},
            enriched_data=metadata,
            detected_at=datetime.utcnow(),
            first_seen=datetime.utcnow()
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert

    def get_threat_alerts(
        self,
        org_id: UUID,
        status: Optional[ThreatStatus] = None,
        severity: Optional[ThreatSeverity] = None,
        limit: int = 100
    ) -> List[ThreatAlert]:
        """Get threat alerts for an organization"""
        query = self.db.query(ThreatAlert).filter(
            ThreatAlert.organization_id == org_id
        )
        
        if status:
            query = query.filter(ThreatAlert.status == status)
        
        if severity:
            query = query.filter(ThreatAlert.severity == severity)
        
        return query.order_by(ThreatAlert.detected_at.desc()).limit(limit).all()

