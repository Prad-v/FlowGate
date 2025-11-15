"""OpAMP Protocol Router - Unified endpoint for OpAMP protocol

This router provides a unified entry point that routes to appropriate transport handlers.
The actual transport-specific implementations are in opamp_websocket.py and opamp_http.py.

According to OpAMP specification: https://opentelemetry.io/docs/specs/opamp/
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.services.opamp_service import OpAMPService
from app.services.opamp_protocol_service import OpAMPProtocolService
from app.utils.auth import get_opamp_token

router = APIRouter(prefix="/opamp/v1", tags=["opamp-protocol"])


@router.post("/opamp")
async def opamp_protocol_unified(
    request: Request,
    token_info: dict = Depends(get_opamp_token),
    db: Session = Depends(get_db),
):
    """
    Unified OpAMP protocol endpoint
    
    This endpoint handles OpAMP protocol messages and routes them appropriately.
    It supports both HTTP and WebSocket transports (WebSocket is handled separately).
    
    For HTTP transport, this endpoint processes AgentToServer messages and returns
    ServerToAgent responses according to the OpAMP specification.
    """
    instance_id = token_info["instance_id"]
    protocol_service = OpAMPProtocolService(db)
    
    # Check if this is a WebSocket upgrade request
    upgrade_header = request.headers.get("Upgrade", "").lower()
    if upgrade_header == "websocket":
        # WebSocket connections are handled by opamp_websocket.py
        # This endpoint is for HTTP POST only
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED,
            detail="WebSocket transport required. Use ws:// or wss:// endpoint.",
            headers={"Upgrade": "websocket"}
        )
    
    # Handle HTTP POST transport
    try:
        body = await request.body()
        
        if not body:
            # Initial connection - send ServerToAgent message
            server_message = protocol_service.build_initial_server_message(instance_id)
            return protocol_service.serialize_server_message(server_message)
        
        # Parse AgentToServer message
        agent_message = protocol_service.parse_agent_message(body)
        
        # Process message and get ServerToAgent response
        server_message = protocol_service.process_agent_to_server(
            instance_id,
            agent_message
        )
        
        # Return ServerToAgent response
        # For now, return as JSON (in production, use protobuf)
        return server_message
    
    except Exception as e:
        # Return error response per OpAMP spec
        error_response = {
            "error_response": {
                "type": "INTERNAL_ERROR",
                "message": str(e)
            }
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response
        )


@router.get("/opamp")
async def opamp_get(
    request: Request,
    token_info: dict = Depends(get_opamp_token),
    db: Session = Depends(get_db),
):
    """
    OpAMP GET endpoint for health/status checks
    
    This is a simple health check endpoint that doesn't follow the OpAMP protocol.
    It's kept for backward compatibility and monitoring purposes.
    """
    return {
        "status": "ok",
        "instance_id": token_info["instance_id"],
        "protocol": "opamp",
        "transports": ["websocket", "http"]
    }

