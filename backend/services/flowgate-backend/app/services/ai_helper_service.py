"""AI Helper Service

Provides AI-powered assistance to help users understand and use the security platform.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from app.services.settings_service import SettingsService
import httpx
import json

logger = logging.getLogger(__name__)


class AIHelperService:
    """AI Helper service for user assistance"""

    def __init__(self, db: Session):
        self.db = db
        self.settings_service = SettingsService(db)

    async def get_help(
        self,
        org_id: UUID,
        question: str,
        context: Optional[str] = None,
        page: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered help response for user questions.
        
        Args:
            org_id: Organization UUID
            question: User's question
            context: Additional context (e.g., current data, errors)
            page: Current page/module (e.g., 'threat-management', 'access-governance')
            
        Returns:
            Dict with 'answer' and 'suggestions'
        """
        try:
            # Get AI settings - handle case where org doesn't exist
            try:
                ai_settings = self.settings_service.get_ai_provider_config(org_id)
            except ValueError as e:
                # Check if it's an organization not found error
                error_str = str(e)
                if "does not exist" in error_str.lower():
                    return {
                        "answer": "Organization not found. Please ensure you are authenticated and your organization is set up correctly. If you're testing, you may need to create an organization first.",
                        "suggestions": ["Check your authentication", "Create an organization in the system", "Contact your administrator"],
                        "error": "org_not_found"
                    }
                # Re-raise other ValueError exceptions
                raise
            except Exception as e:
                # Check if it's a foreign key violation (org doesn't exist)
                error_str = str(e)
                if "ForeignKeyViolation" in error_str or "foreign key" in error_str.lower():
                    return {
                        "answer": "Organization not found. Please ensure you are authenticated and your organization is set up correctly.",
                        "suggestions": ["Check your authentication", "Contact your administrator"],
                        "error": "org_not_found"
                    }
                # Re-raise other exceptions
                raise
            
            if not ai_settings:
                return {
                    "answer": "AI assistance is not configured. Please configure an LLM provider in Settings > AI Integration.",
                    "suggestions": ["Configure AI provider in Settings"],
                    "error": "ai_not_configured"
                }
            
            # Check if enabled (default to True if not specified)
            if ai_settings.get("enabled", True) is False:
                return {
                    "answer": "AI assistance is disabled. Please enable it in Settings > AI Integration.",
                    "suggestions": ["Enable AI provider in Settings"],
                    "error": "ai_disabled"
                }
            
            # Build system prompt with context about security modules
            system_prompt = self._build_system_prompt(page, context)
            
            # Build user message
            user_message = question
            if context:
                user_message += f"\n\nContext: {context}"
            
            # Call LLM
            response = await self._call_llm(
                org_id=org_id,
                system_prompt=system_prompt,
                user_message=user_message,
                ai_settings=ai_settings
            )
            
            # Parse response and extract suggestions
            answer, suggestions = self._parse_response(response)
            
            return {
                "answer": answer,
                "suggestions": suggestions,
                "page": page
            }
            
        except Exception as e:
            logger.error(f"Error getting AI help: {e}", exc_info=True)
            return {
                "answer": f"I encountered an error: {str(e)}. Please try again or contact support.",
                "suggestions": ["Check AI provider configuration", "Try rephrasing your question"],
                "error": str(e)
            }

    def _build_system_prompt(self, page: Optional[str], context: Optional[str]) -> str:
        """Build system prompt with knowledge about security modules"""
        
        base_prompt = """You are an AI assistant for FlowGate, a security and observability platform. 
You help users understand and use the security modules effectively.

## Security Modules Overview:

### 1. Identity Governance Agent (IGA)
- **Purpose**: Manages access requests, role drift detection, and entitlement risk analysis
- **Key Features**:
  - Access request risk scoring (JITA/JITP)
  - Role drift detection (identifies when user roles change unexpectedly)
  - Entitlement risk analysis (analyzes user permissions and access paths)
  - Graph-based access path analysis using Neo4j
- **Use Cases**: 
  - Approving/denying access requests
  - Detecting unauthorized privilege escalation
  - Analyzing access risk before granting permissions
- **Data Sources**: Identity provider logs (Okta, Azure AD, Keycloak), access logs

### 2. Threat Vector Agent (TVA)
- **Purpose**: Detects security threats using MITRE ATT&CK framework and behavioral analytics
- **Key Features**:
  - MITRE ATT&CK TTP (Tactics, Techniques, Procedures) mapping
  - Anomaly detection using machine learning embeddings
  - Multi-step attack pattern detection
  - Threat intelligence feed integration
- **Use Cases**:
  - Detecting suspicious login attempts
  - Identifying attack patterns
  - Mapping threats to MITRE ATT&CK framework
- **Data Sources**: Network logs, endpoint logs, application logs

### 3. Correlation & RCA Agent (CRA)
- **Purpose**: Correlates multiple security events and performs root cause analysis
- **Key Features**:
  - Cross-log correlation (connects related events across different sources)
  - Attack timeline reconstruction
  - Root cause analysis
  - Blast radius estimation (determines impact scope)
- **Use Cases**:
  - Investigating security incidents
  - Understanding attack progression
  - Determining root cause of breaches
- **Data Sources**: Threat alerts, logs from multiple sources

### 4. Persona Baseline Agent (PBA)
- **Purpose**: Learns normal user and service behavior patterns to detect anomalies
- **Key Features**:
  - User behavior baseline learning
  - Service behavior baseline learning
  - Anomaly detection via vector embeddings
  - Continuous baseline updates
- **Use Cases**:
  - Detecting unusual user activity
  - Identifying compromised accounts
  - Finding service behavior deviations
- **Data Sources**: User activity logs, service logs

### 5. SOAR Automation Agent (SAA)
- **Purpose**: Automates security response actions through playbooks
- **Key Features**:
  - Playbook execution engine
  - Integration with JIRA, Slack, PagerDuty
  - Automated response actions (quarantine, key rotation, IP blocking)
  - Audit trail logging
- **Use Cases**:
  - Automating incident response
  - Executing security playbooks
  - Integrating with external tools
- **Triggers**: Threat alerts, incidents, access requests, anomalies

## Data Flow:
1. Logs are ingested via OTel Collector Gateway
2. Logs are normalized and transformed
3. Normalized logs are published to NATS event bus
4. AI agents subscribe to relevant log streams
5. Agents analyze logs and create alerts/incidents
6. SOAR playbooks can be triggered automatically

## Storage:
- **PostgreSQL**: Stores alerts, incidents, access requests, playbooks, baselines
- **Neo4j**: Stores access graph (users, roles, resources, permissions)
- **pgvector**: Stores embeddings for similarity search

## Best Practices:
- Start with Threat Vector Agent to detect threats
- Use Identity Governance Agent for access management
- Create SOAR playbooks for common response scenarios
- Review Persona Baselines regularly to ensure accuracy
- Use Correlation & RCA Agent for incident investigation

Provide clear, concise, and helpful answers. If the user asks about a specific page/module, focus on that module.
If they ask "how do I...", provide step-by-step instructions.
If they ask "what is...", provide clear explanations with examples.
"""
        
        # Add page-specific context
        if page:
            page_context = self._get_page_context(page)
            base_prompt += f"\n\n## Current Context:\n{page_context}\n"
        
        return base_prompt

    def _get_page_context(self, page: str) -> str:
        """Get context-specific information for the current page"""
        
        contexts = {
            "threat-management": """
You are helping on the Threat Management page (Threat Vector Agent).
This page shows:
- Threat alerts with severity levels (Low, Medium, High, Critical)
- MITRE ATT&CK technique mappings
- Anomaly scores and confidence levels
- Source types (identity, network, endpoint, application)
- Filtering by severity, status, source type

Common tasks:
- Viewing threat alerts
- Filtering alerts by severity or status
- Understanding MITRE ATT&CK mappings
- Investigating specific threats
""",
            "access-governance": """
You are helping on the Access Governance page (Identity Governance Agent).
This page shows:
- Access requests (JITA/JITP)
- Risk scores and risk factors
- Role drift detections
- Approval workflow

Common tasks:
- Approving/denying access requests
- Understanding risk scores
- Reviewing role drift alerts
- Managing access entitlements
""",
            "incidents": """
You are helping on the Incidents page (Correlation & RCA Agent).
This page shows:
- Correlated security incidents
- Root cause analysis
- Attack timelines
- Blast radius information

Common tasks:
- Viewing incidents
- Investigating root causes
- Reviewing attack timelines
- Understanding incident severity
""",
            "personas": """
You are helping on the Personas page (Persona Baseline Agent).
This page shows:
- User and service behavior baselines
- Anomaly detections
- Baseline statistics
- Behavior patterns

Common tasks:
- Viewing behavior baselines
- Reviewing anomalies
- Understanding baseline statistics
- Managing baseline thresholds
""",
            "soar-playbooks": """
You are helping on the SOAR Playbooks page (SOAR Automation Agent).
This page shows:
- Playbook definitions
- Execution history
- Trigger conditions
- Action results

Common tasks:
- Creating playbooks
- Viewing execution history
- Configuring triggers
- Reviewing action results
"""
        }
        
        return contexts.get(page, "You are helping with the FlowGate security platform.")

    async def _call_llm(
        self,
        org_id: UUID,
        system_prompt: str,
        user_message: str,
        ai_settings: Dict[str, Any]
    ) -> str:
        """Call LLM API"""
        
        provider_type = ai_settings.get("provider_type", "openai")
        api_key = ai_settings.get("api_key")
        model = ai_settings.get("model", "gpt-3.5-turbo")
        endpoint = ai_settings.get("endpoint")
        
        if not api_key:
            raise ValueError("API key not configured")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        if provider_type == "litellm" and endpoint:
            # Use LiteLLM endpoint
            url = f"{endpoint}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        elif provider_type == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _parse_response(self, response: str) -> tuple[str, List[str]]:
        """Parse LLM response and extract suggestions"""
        
        # Try to extract suggestions if formatted
        suggestions = []
        answer = response
        
        # Look for suggestions section
        if "Suggestions:" in response or "Next steps:" in response:
            parts = response.split("Suggestions:" if "Suggestions:" in response else "Next steps:")
            if len(parts) > 1:
                answer = parts[0].strip()
                suggestions_text = parts[1].strip()
                # Extract bullet points
                for line in suggestions_text.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                        suggestion = line.lstrip("-*• ").strip()
                        if suggestion:
                            suggestions.append(suggestion)
        
        # If no suggestions found, generate some from the answer
        if not suggestions:
            # Simple heuristic: extract actionable items
            lines = answer.split("\n")
            for line in lines[:3]:  # First 3 lines
                if any(word in line.lower() for word in ["check", "review", "configure", "create", "view"]):
                    suggestions.append(line.strip())
        
        return answer, suggestions[:3]  # Max 3 suggestions

