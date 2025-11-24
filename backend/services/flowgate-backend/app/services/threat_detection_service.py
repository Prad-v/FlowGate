"""Threat Detection Service

Subscribes to NATS for normalized logs and routes them to AI agents for threat detection.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.messaging import get_nats_client, format_log_subject
from app.services.threat_vector_service import ThreatVectorService

logger = logging.getLogger(__name__)


class ThreatDetectionService:
    """Service that subscribes to NATS and routes logs to threat detection agents"""

    def __init__(self, db: Session):
        self.db = db
        self.nats_client = get_nats_client()
        self.threat_vector_service = ThreatVectorService(db)
        self._subscriptions = []
        self._running = False

    async def start(self) -> None:
        """Start subscribing to NATS for normalized logs"""
        if self._running:
            return

        try:
            await self.nats_client.connect()
            self._running = True

            # Subscribe to all normalized log subjects
            # Pattern: logs.normalized.*.*
            await self._subscribe_to_logs()
            logger.info("Threat Detection Service started and subscribed to NATS")

        except Exception as e:
            logger.error(f"Failed to start Threat Detection Service: {e}")
            raise

    async def stop(self) -> None:
        """Stop subscribing and cleanup"""
        self._running = False
        # Unsubscribe from all subscriptions
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception as e:
                logger.warning(f"Error unsubscribing: {e}")
        self._subscriptions.clear()
        logger.info("Threat Detection Service stopped")

    async def _subscribe_to_logs(self) -> None:
        """Subscribe to normalized log subjects"""
        # Subscribe to pattern: logs.normalized.>
        # This will match all normalized logs regardless of source type or org
        subject_pattern = "logs.normalized.>"
        
        async def message_handler(data: Dict[str, Any], subject: str) -> None:
            """Handle incoming normalized log messages"""
            try:
                await self._process_normalized_log(data, subject)
            except Exception as e:
                logger.error(f"Error processing normalized log from {subject}: {e}")

        try:
            sub = await self.nats_client.subscribe(
                subject_pattern,
                callback=message_handler
            )
            self._subscriptions.append(sub)
            logger.info(f"Subscribed to {subject_pattern}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {subject_pattern}: {e}")
            raise

    async def _process_normalized_log(self, data: Dict[str, Any], subject: str) -> None:
        """Process a normalized log message"""
        try:
            source_type = data.get("source", "unknown")
            org_id = data.get("org_id")
            log_data = data.get("log_data", "")
            metadata = data.get("metadata", {})

            if not org_id:
                logger.warning(f"Received log without org_id from {subject}")
                return

            # Route to Threat Vector Agent for analysis
            await self.threat_vector_service.analyze_log(
                org_id=org_id,
                source_type=source_type,
                log_data=log_data,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error processing normalized log: {e}")

