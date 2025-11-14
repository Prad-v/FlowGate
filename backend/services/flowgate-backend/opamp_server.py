"""OpAMP server for config distribution."""
from fastapi import FastAPI, HTTPException
from typing import Dict, Optional
from uuid import UUID
import logging
from config import settings

logger = logging.getLogger(__name__)

# This is a placeholder OpAMP server implementation
# In production, this would implement the full OpAMP protocol
# For now, we'll create a basic structure

opamp_app = FastAPI(title="Flowgate OpAMP Server")

# In-memory store for gateway configs (in production, use database)
gateway_configs: Dict[str, Dict] = {}


@opamp_app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@opamp_app.post("/v1/instances/{instance_id}/config")
async def update_gateway_config(instance_id: str, config: dict):
    """Update gateway configuration (OpAMP protocol placeholder)."""
    gateway_configs[instance_id] = config
    logger.info(f"Updated config for gateway {instance_id}")
    return {"status": "ok"}


@opamp_app.get("/v1/instances/{instance_id}/config")
async def get_gateway_config(instance_id: str):
    """Get gateway configuration."""
    if instance_id not in gateway_configs:
        raise HTTPException(status_code=404, detail="Gateway config not found")
    return gateway_configs[instance_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "opamp_server:opamp_app",
        host=settings.opamp_server_host,
        port=settings.opamp_server_port,
    )


