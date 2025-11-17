"""OpAMP HTTP Transport Router (Plain HTTP)

Implements OpAMP protocol over HTTP POST with long-polling as per specification:
https://opentelemetry.io/docs/specs/opamp/
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json
import logging
import asyncio

from app.database import get_db
from app.services.opamp_service import OpAMPService
from app.services.opamp_protocol_service import OpAMPProtocolService
from app.utils.auth import get_opamp_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opamp/v1", tags=["opamp-http"])


@router.post("/opamp")
async def opamp_http_post(
    request: Request,
    token_info: dict = Depends(get_opamp_token),
    db: Session = Depends(get_db),
):
    """
    OpAMP HTTP POST endpoint (Plain HTTP transport)
    
    Handles OpAMP protocol over HTTP POST as per specification.
    Supports long-polling for server-to-agent messages.
    """
    instance_id = token_info["instance_id"]
    protocol_service = OpAMPProtocolService(db)
    
    # Check if this is a long-polling request
    timeout = request.query_params.get("timeout", "30")
    try:
        timeout_seconds = int(timeout)
    except ValueError:
        timeout_seconds = 30
    
    # Read request body
    try:
        body = await request.body()
        if not body:
            # Initial connection - send ServerToAgent message
            server_message = protocol_service.build_initial_server_message(instance_id)
            return Response(
                content=protocol_service.serialize_server_message(server_message),
                media_type="application/x-protobuf",
                headers={
                    "Content-Type": "application/x-protobuf",
                }
            )
        
        # Parse AgentToServer message
        agent_message = protocol_service.parse_agent_message(body)
        
        # Check if parsing failed completely - if so, return error response
        if agent_message is None:
            logger.error(f"Skipping unparseable message from {instance_id} to avoid incorrect capability inference")
            error_response = opamp_pb2.ServerToAgent()
            error_response.error_response.type = opamp_pb2.ServerErrorResponse.ServerErrorResponseType.ServerErrorResponseType_INTERNAL_ERROR
            error_response.error_response.message = "Failed to parse AgentToServer message"
            return Response(
                content=protocol_service.serialize_server_message(error_response),
                media_type="application/x-protobuf",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Process message
        server_message = protocol_service.process_agent_to_server(
            instance_id,
            agent_message
        )
        
        # Return ServerToAgent response
        return Response(
            content=protocol_service.serialize_server_message(server_message),
            media_type="application/x-protobuf",
            headers={
                "Content-Type": "application/x-protobuf",
            }
        )
    
    except Exception as e:
        logger.error(f"Error processing OpAMP HTTP message: {e}", exc_info=True)
        
        # Return error response per spec
        error_response = {
            "error_response": {
                "type": "INTERNAL_ERROR",
                "message": str(e)
            }
        }
        
        return Response(
            content=protocol_service.serialize_server_message(error_response),
            media_type="application/x-protobuf",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/opamp/poll")
async def opamp_http_poll(
    request: Request,
    token_info: dict = Depends(get_opamp_token),
    db: Session = Depends(get_db),
):
    """
    OpAMP HTTP long-polling endpoint
    
    Implements long-polling for server-to-agent messages as per specification.
    Client sends empty POST and waits for server to send updates.
    """
    instance_id = token_info["instance_id"]
    protocol_service = OpAMPProtocolService(db)
    
    # Get timeout from query parameter
    timeout = request.query_params.get("timeout", "30")
    try:
        timeout_seconds = int(timeout)
    except ValueError:
        timeout_seconds = 30
    
    async def generate_response():
        """Generator for long-polling response"""
        # Wait for config updates or timeout
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if there's a new config for this gateway
            config = protocol_service.opamp_service.get_config_for_gateway(instance_id)
            
            if config:
                # Build ServerToAgent message with config
                server_message = protocol_service.build_initial_server_message(instance_id)
                yield protocol_service.serialize_server_message(server_message)
                break
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_seconds:
                # Send empty response to keep connection alive
                empty_message = {
                    "instance_uid": "",
                    "capabilities": 0,
                }
                yield protocol_service.serialize_server_message(empty_message)
                break
            
            # Wait a bit before checking again
            await asyncio.sleep(1)
    
    return StreamingResponse(
        generate_response(),
        media_type="application/x-protobuf",
        headers={
            "Content-Type": "application/x-protobuf",
        }
    )


@router.post("/opamp/status")
async def opamp_http_status(
    request: Request,
    token_info: dict = Depends(get_opamp_token),
    db: Session = Depends(get_db),
):
    """
    OpAMP HTTP status endpoint for throttling
    
    Returns HTTP 503 or 429 with Retry-After header when server is overloaded.
    """
    # For now, always return OK
    # In production, implement actual throttling logic
    return {"status": "ok"}

