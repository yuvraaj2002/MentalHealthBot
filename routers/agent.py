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
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Mental Health Agent"])

# Initialize services
websocket_service = WebSocketService()
agent_service = MentalHealthAgentService()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """Simple WebSocket endpoint for mental health bot connection"""
    
    try:
        # Accept the connection
        await websocket.accept()
        
        # Send simple success response
        success_message = {
            "status": "connected",
            "message": "Successfully connected to Mental Health Bot",
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await websocket.send_text(json.dumps(success_message))
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any message from client
                data = await websocket.receive_text()
                
                # Echo back a simple response
                response = {
                    "status": "received",
                    "message": f"Received: {data}",
                    "user_id": user_id,
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close()
        except:
            pass


@router.post("/send-message")
async def send_message_to_user(
    user_id: str,
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to a specific user via WebSocket (admin/provider only)"""
    
    # Check if current user is admin or provider
    if not (current_user.is_admin or getattr(current_user, 'is_provider', False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to send messages"
        )
    
    # Check if user is connected
    if not websocket_service.is_connected(user_id):
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
    
    success = await websocket_service.send_json_message(admin_message, user_id)
    
    if success:
        return {
            "message": "Message sent successfully",
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat()
        }
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
