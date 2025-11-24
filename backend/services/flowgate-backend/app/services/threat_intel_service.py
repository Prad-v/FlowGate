"""Threat Intelligence Service

Provides MITRE ATT&CK framework data and threat intelligence feeds.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from pathlib import Path

logger = logging.getLogger(__name__)


class ThreatIntelService:
    """Threat Intelligence service"""

    def __init__(self, db: Session):
        self.db = db
        self._mitre_data: Optional[Dict[str, Any]] = None

    def get_mitre_framework(self) -> Dict[str, Any]:
        """Get MITRE ATT&CK framework data"""
        if self._mitre_data is None:
            # Load MITRE framework (simplified - in production, load from API or file)
            self._mitre_data = self._load_mitre_framework()
        return self._mitre_data

    def _load_mitre_framework(self) -> Dict[str, Any]:
        """Load MITRE ATT&CK framework data"""
        # Simplified MITRE framework structure
        # In production, this would load from MITRE ATT&CK API or local JSON file
        return {
            "tactics": [
                "Initial Access",
                "Execution",
                "Persistence",
                "Privilege Escalation",
                "Defense Evasion",
                "Credential Access",
                "Discovery",
                "Lateral Movement",
                "Collection",
                "Command and Control",
                "Exfiltration",
                "Impact"
            ],
            "techniques": {
                "T1055": {
                    "id": "T1055",
                    "name": "Process Injection",
                    "tactics": ["Defense Evasion", "Privilege Escalation"],
                    "description": "Adversaries may inject code into processes"
                },
                "T1078": {
                    "id": "T1078",
                    "name": "Valid Accounts",
                    "tactics": ["Defense Evasion", "Persistence", "Privilege Escalation", "Initial Access"],
                    "description": "Adversaries may steal and use credentials"
                },
                # Add more techniques as needed
            }
        }

    def get_technique_by_id(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Get MITRE technique by ID"""
        framework = self.get_mitre_framework()
        return framework.get("techniques", {}).get(technique_id)

    def search_techniques(
        self,
        query: str,
        tactic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search MITRE techniques"""
        framework = self.get_mitre_framework()
        techniques = framework.get("techniques", {})
        
        results = []
        query_lower = query.lower()
        
        for tech_id, tech_data in techniques.items():
            if query_lower in tech_data.get("name", "").lower() or \
               query_lower in tech_data.get("description", "").lower():
                if not tactic or tactic in tech_data.get("tactics", []):
                    results.append(tech_data)
        
        return results

