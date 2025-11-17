"""OpAMP WebSocket Transport Router

Implements OpAMP protocol over WebSocket as per specification:
https://opentelemetry.io/docs/specs/opamp/
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
import logging

from app.services.opamp_service import OpAMPService
from app.services.opamp_protocol_service import OpAMPProtocolService
from app.services.gateway_service import GatewayService
from app.services.websocket_manager import get_websocket_manager
from app.models.gateway import OpAMPConnectionStatus
from app.protobufs import opamp_pb2

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
        ws_manager = get_websocket_manager()
        
        # Register WebSocket connection
        ws_manager.register_connection(instance_id, websocket)
        
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
                        if not message_data or len(message_data) == 0:
                            # Skip empty messages
                            continue
                        
                        # Fix: Remove leading null bytes if present (WebSocket framing issue)
                        # Protobuf messages should never start with 0x00
                        while len(message_data) > 0 and message_data[0] == 0x00:
                            logger.warning(f"[WS] Removing leading null byte from message (size: {len(message_data)} -> {len(message_data)-1})")
                            message_data = message_data[1:]
                        
                        if len(message_data) == 0:
                            logger.warning(f"[WS] Message became empty after removing null bytes, skipping")
                            continue
                        
                        logger.info(f"[WS] Received binary message from {instance_id} ({len(message_data)} bytes, first byte: 0x{message_data[0]:02x})")
                        agent_message = protocol_service.parse_agent_message(message_data)
                        
                        # Check if parsing failed completely - if so, skip processing this message
                        if agent_message is None:
                            logger.error(f"[WS] Skipping unparseable message from {instance_id} to avoid incorrect capability inference")
                            continue
                        
                        logger.info(
                            f"[WS] Parsed AgentToServer message from {instance_id}: "
                            f"seq={agent_message.sequence_num}, "
                            f"capabilities=0x{agent_message.capabilities:X} ({agent_message.capabilities}), "
                            f"has_effective_config={agent_message.HasField('effective_config')}, "
                            f"has_remote_config_status={agent_message.HasField('remote_config_status')}, "
                            f"has_health={agent_message.HasField('health')}, "
                            f"has_agent_description={agent_message.HasField('agent_description')}"
                        )
                    elif "text" in data:
                        # JSON message (fallback, but OpAMP extension uses Protobuf)
                        message_data = data["text"].encode('utf-8')
                        if not message_data or len(message_data) == 0:
                            continue
                        logger.info(f"[WS] Received text message from {instance_id} ({len(message_data)} bytes)")
                        agent_message = protocol_service.parse_agent_message(message_data)
                        
                        # Check if parsing failed completely - if so, skip processing this message
                        if agent_message is None:
                            logger.error(f"[WS] Skipping unparseable message from {instance_id} to avoid incorrect capability inference")
                            continue
                        
                        logger.info(f"[WS] Parsed AgentToServer message from {instance_id}: seq={agent_message.sequence_num}, has_effective_config={agent_message.HasField('effective_config')}")
                    else:
                        # No valid message data, skip
                        continue
                    
                    # Process message and get response
                    try:
                        logger.info(f"[WS] Processing AgentToServer message from {instance_id} (seq={agent_message.sequence_num})")
                        server_message = protocol_service.process_agent_to_server(
                            instance_id,
                            agent_message
                        )
                        
                        # Log ServerToAgent response details
                        flags_info = f"flags=0x{server_message.flags:X}" if server_message.flags else "flags=0"
                        has_remote_config = server_message.HasField("remote_config")
                        logger.info(f"[WS] Built ServerToAgent response for {instance_id}: {flags_info}, has_remote_config={has_remote_config}, capabilities=0x{server_message.capabilities:X}")
                        
                        # Only send response if message is valid and not empty
                        if server_message:
                            server_message_bytes = protocol_service.serialize_server_message(server_message)
                            if server_message_bytes and len(server_message_bytes) > 0:
                                logger.info(f"[WS] Sending ServerToAgent response to {instance_id} ({len(server_message_bytes)} bytes)")
                                await websocket.send_bytes(server_message_bytes)
                                logger.info(f"[WS] ✓ Successfully sent ServerToAgent response to {instance_id}")
                    except Exception as process_error:
                        # Handle processing errors separately
                        logger.error(f"Error processing OpAMP message: {process_error}", exc_info=True)
                        error_response = protocol_service.create_error_response(
                            error_type=opamp_pb2.ServerErrorResponseType_BadRequest,
                            error_message=f"Failed to process message: {str(process_error)}"
                        )
                        error_bytes = protocol_service.serialize_server_message(error_response)
                        await websocket.send_bytes(error_bytes)
                    
                except WebSocketDisconnect:
                    logger.info(f"OpAMP WebSocket disconnected for instance: {instance_id}")
                    # Unregister WebSocket connection
                    ws_manager.unregister_connection(instance_id)
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
                    # Send Protobuf error response (not JSON!)
                    error_response = protocol_service.create_error_response(
                        error_type=opamp_pb2.ServerErrorResponseType_Unknown,
                        error_message=str(e)
                    )
                    error_bytes = protocol_service.serialize_server_message(error_response)
                    await websocket.send_bytes(error_bytes)
        
        except Exception as e:
            logger.error(f"OpAMP WebSocket error: {e}", exc_info=True)
            # Update connection status to failed
            gateway_service.update_opamp_status(
                instance_id,
                OpAMPConnectionStatus.FAILED,
                transport_type="websocket"
            )
    finally:
        # Unregister WebSocket connection on cleanup
        if instance_id:
            ws_manager = get_websocket_manager()
            ws_manager.unregister_connection(instance_id)
        # Update connection status to disconnected on cleanup
        try:
            if instance_id:
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
        if instance_id:
            logger.info(f"OpAMP WebSocket connection closed for instance: {instance_id}")

