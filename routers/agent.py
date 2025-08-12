import sys
import os
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, UTC

# Add project root to path for imports
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

from models.database_models import User, get_db
from services.auth_service import get_current_active_user
from services.websocket_service import WebSocketService
from services.mental_health_agent_service import MentalHealthAgentService
from services.validation_service import ValidationService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Mental Health Agent"])

# Initialize services
websocket_service = WebSocketService()
agent_service = MentalHealthAgentService()
validation_service = ValidationService()

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, token: str = None):
    """Secure WebSocket endpoint for mental health bot connection"""
    
    try:
        # Validate chat ID
        is_valid_chat, chat_error = validation_service.validate_chat_id(chat_id)
        if not is_valid_chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=chat_error)
            return
        
        # Get database session
        db = next(get_db())
        
        # Validate WebSocket connection with token from query parameter
        is_valid, user, error_reason = await validation_service.validate_websocket_connection(websocket, db, token)
        if not is_valid:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=error_reason)
            return
        
        # Store connection in websocket service
        user_info = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
        await websocket_service.connect(websocket, chat_id, user_info)
        
        # Send welcome message
        welcome_message = validation_service.create_success_response(
            "connection",
            f"Welcome {user.first_name}! Successfully connected to Mental Health Bot",
            chat_id=chat_id,
            user_id=user.id
        )
        
        await websocket.send_text(json.dumps(welcome_message))
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any message from client
                data = await websocket.receive_text()
                
                # Validate message format
                is_valid_msg, msg_error = validation_service.validate_message_format(data)
                if not is_valid_msg:
                    error_response = validation_service.create_error_response(
                        "validation_error", 
                        msg_error,
                        chat_id=chat_id,
                        user_id=user.id
                    )
                    await websocket.send_text(json.dumps(error_response))
                    continue
                
                # Process message with agent service
                bot_response = await agent_service.process_user_message(data, str(user.id), db)
                
                # Send bot response back to user
                response = validation_service.create_success_response(
                    "bot_response",
                    bot_response.get("content", "I'm here to help you."),
                    chat_id=chat_id,
                    user_id=user.id
                )
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_response = validation_service.create_error_response(
                    "processing_error",
                    "An error occurred while processing your message",
                    chat_id=chat_id,
                    user_id=user.id
                )
                await websocket.send_text(json.dumps(error_response))
                break
                
    except WebSocketDisconnect:
        websocket_service.disconnect(chat_id)
        logger.info(f"User {chat_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {chat_id}: {e}")
        websocket_service.disconnect(chat_id)
        try:
            await websocket.close()
        except:
            pass


@router.post("/send-message")
async def send_message_to_user(
    chat_id: str,
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to a specific user via WebSocket (admin/provider only)"""
    
    # Validate chat ID
    is_valid_chat, chat_error = validation_service.validate_chat_id(chat_id)
    if not is_valid_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=chat_error
        )
    
    # Validate message format
    is_valid_msg, msg_error = validation_service.validate_message_format(message)
    if not is_valid_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg_error
        )
    
    # Check user permissions
    has_permission, perm_error = validation_service.validate_user_permissions(current_user, "provider")
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=perm_error
        )
    
    # Check if user is connected
    if not websocket_service.is_connected(chat_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not currently connected"
        )
    
    # Send message
    admin_message = {
        "type": "admin_message",
        "content": message,
        "from_user": current_user.id,
        "from_user_name": f"{current_user.first_name} {current_user.last_name}",
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    success = await websocket_service.send_json_message(admin_message, chat_id)
    
    if success:
        return validation_service.create_success_response(
            "message_sent",
            "Message sent successfully",
            chat_id=chat_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )










######################################### Future Scope implementations ##################################
# @router.get("/connections")
# async def get_connection_info():
#     """Get detailed connection information"""
#     return {
#         "active_connections": websocket_service.get_all_connection_info(),
#         "connection_count": websocket_service.get_connection_count(),
#         "connected_users": websocket_service.get_connected_users()
#     }

# @router.get("/conversation-history/{user_id}")
# async def get_user_conversation_history(
#     user_id: str,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Get conversation history for a specific user (admin/provider only)"""
    
#     # Check if current user is admin or provider
#     if not (current_user.is_admin or getattr(current_user, 'is_provider', False)):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions to view conversation history"
#         )
    
#     conversation_history = agent_service.get_conversation_history(user_id)
    
#     return {
#         "user_id": user_id,
#         "conversation_history": conversation_history,
#         "total_messages": len(conversation_history),
#         "timestamp": datetime.now(UTC).isoformat()
#     }

# @router.delete("/conversation-history/{user_id}")
# async def clear_user_conversation_history(
#     user_id: str,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Clear conversation history for a specific user (admin only)"""
    
#     # Check if current user is admin
#     if not current_user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only admins can clear conversation history"
#         )
    
#     agent_service.clear_conversation_history(user_id)
    
#     return {
#         "message": "Conversation history cleared successfully",
#         "user_id": user_id,
#         "timestamp": datetime.now(UTC).isoformat()
#     }

# @router.post("/ping-connections")
# async def ping_all_connections(
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Ping all active connections to check health (admin only)"""
    
#     # Check if current user is admin
#     if not current_user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only admins can ping connections"
#         )
    
#     ping_results = await websocket_service.ping_all_connections()
    
#     return {
#         "ping_results": ping_results,
#         "total_connections": len(ping_results),
#         "successful_pings": sum(1 for success in ping_results.values() if success),
#         "timestamp": datetime.now(UTC).isoformat()
#     }
