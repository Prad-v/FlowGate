"""OpAMP WebSocket Transport Router

Implements OpAMP protocol over WebSocket as per specification:
https://opentelemetry.io/docs/specs/opamp/
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
import logging

from app.services.opamp_service import OpAMPService
from app.services.opamp_protocol_service import OpAMPProtocolService
from app.services.gateway_service import GatewayService
from app.models.gateway import OpAMPConnectionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opamp/v1", tags=["opamp-websocket"])


@router.websocket("/opamp")
async def opamp_websocket(websocket: WebSocket):
    """
    OpAMP WebSocket endpoint
    
    Handles OpAMP protocol over WebSocket connection as per specification.
    Supports bidirectional communication for real-time configuration updates.
    """
    await websocket.accept()
    
    # Extract and validate token
    token = None
    token = websocket.query_params.get("token")
    if not token:
        headers = dict(websocket.headers)
        auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="OpAMP token required")
        return
    
    # Get database session for token validation
    from app.database import SessionLocal
    db = SessionLocal()
    instance_id = None
    try:
        # Validate token
        opamp_service = OpAMPService(db)
        token_info = opamp_service.validate_opamp_token(token)
        if not token_info:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid OpAMP token")
            return
        
        instance_id = token_info["instance_id"]
        protocol_service = OpAMPProtocolService(db)
        gateway_service = GatewayService(db)
        
        # Update connection status to connected
        gateway_service.update_opamp_status(
            instance_id,
            OpAMPConnectionStatus.CONNECTED,
            transport_type="websocket"
        )
        
        logger.info(f"OpAMP WebSocket connection established for instance: {instance_id}")
        
        try:
            # Send initial ServerToAgent message
            initial_message = protocol_service.build_initial_server_message(instance_id)
            # Send as Protobuf bytes (OpAMP extension expects binary Protobuf)
            server_message_bytes = protocol_service.serialize_server_message(initial_message)
            await websocket.send_bytes(server_message_bytes)
            
            # Main message loop
            while True:
                # Receive AgentToServer message
                try:
                    data = await websocket.receive()
                    
                    if "bytes" in data:
                        # Binary protobuf message (expected format)
                        message_data = data["bytes"]
                        agent_message = protocol_service.parse_agent_message(message_data)
                    elif "text" in data:
                        # JSON message (fallback, but OpAMP extension uses Protobuf)
                        message_data = data["text"].encode('utf-8')
                        agent_message = protocol_service.parse_agent_message(message_data)
                    else:
                        continue
                    
                    # Process message and get response
                    server_message = protocol_service.process_agent_to_server(
                        instance_id,
                        agent_message
                    )
                    
                    # Send ServerToAgent response as Protobuf bytes
                    server_message_bytes = protocol_service.serialize_server_message(server_message)
                    await websocket.send_bytes(server_message_bytes)
                    
                except WebSocketDisconnect:
                    logger.info(f"OpAMP WebSocket disconnected for instance: {instance_id}")
                    # Update connection status to disconnected
                    gateway_service.update_opamp_status(
                        instance_id,
                        OpAMPConnectionStatus.DISCONNECTED,
                        transport_type="websocket"
                    )
                    break
                except Exception as e:
                    logger.error(f"Error processing OpAMP message: {e}", exc_info=True)
                    # Update connection status to failed
                    gateway_service.update_opamp_status(
                        instance_id,
                        OpAMPConnectionStatus.FAILED,
                        transport_type="websocket"
                    )
                    # Send error response
                    error_message = {
                        "error_response": {
                            "type": "INTERNAL_ERROR",
                            "message": str(e)
                        }
                    }
                    await websocket.send_json(error_message)
        
        except Exception as e:
            logger.error(f"OpAMP WebSocket error: {e}", exc_info=True)
            # Update connection status to failed
            gateway_service.update_opamp_status(
                instance_id,
                OpAMPConnectionStatus.FAILED,
                transport_type="websocket"
            )
    finally:
        # Update connection status to disconnected on cleanup
        try:
            gateway_service.update_opamp_status(
                instance_id,
                OpAMPConnectionStatus.DISCONNECTED,
                transport_type="websocket"
            )
        except:
            pass
        db.close()
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"OpAMP WebSocket connection closed for instance: {instance_id}")

