import sys
import os
import json
import logging
from typing import Dict, Any, Optional
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
from services.redis_service import RedisService
from services.db_service import DatabaseService
from services.openai_service import LLMService
from config import settings
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_registry import *

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Mental Health Agent"])

# Initialize services
websocket_service = WebSocketService()
agent_service = MentalHealthAgentService()
validation_service = ValidationService()
redis_service = RedisService()
llm_service = LLMService()

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """WebSocket endpoint for mental health bot connection (no auth for local testing)"""
    
    try:
        # Validate chat ID
        is_valid_chat, chat_error = validation_service.validate_chat_id(chat_id)
        if not is_valid_chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=chat_error)
            return
        
        # Get database session
        db = next(get_db())
        
        # Create a mock user for testing
        mock_user = {
            "id": 1,
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com"
        }
        
        # Store connection in websocket service
        await websocket_service.connect(websocket, chat_id, mock_user)

        # Checking if we are talking about the morning or evening checkin
        morning_checking = False
        try:
            if len(chat_id.split('_')) >= 3 and chat_id.split('_')[2] == '1':
                morning_checking = False
            else:
                morning_checking = True
        except:
            morning_checking = True  # Default to morning if parsing fails

        # Getting the checkin context from the database
        checkin_context = DatabaseService.get_last_daily_checkin(db, mock_user['id'], morning_checking)
        
        # Check if chat_id exists in Redis
        chat_exists = redis_service.key_exists(chat_id)
        logger.info(f"Chat ID: {chat_id}, Morning checking: {morning_checking}, Redis exists: {chat_exists}")
        
        if not chat_exists:
            # Greeting agent will take over using the (Checkin context)
            messages = [
                SystemMessage(greeting_agent_prompt.format(checkin_context=checkin_context)),
                HumanMessage("Please generate the greeting based on my check-in.")
            ]
            
            # Stream the response chunk by chunk
            full_response = ""
            async for chunk in llm_service.chatbot_response(messages):
                if chunk:
                    # Send each chunk as plain text (no JSON metadata)
                    await websocket.send_text(chunk)
                    full_response += chunk
            
            # Store the greeting in Redis with sliding window approach
            redis_service.append_conversation(
                chat_id, 
                "Initial greeting request", 
                full_response, 
                expire_seconds=14400
            )
        else:
            # Conversation agent will take over using (Checkin context, Conversational context)
            conversational_context = redis_service.get_conversation_context(chat_id)
            messages = [
                SystemMessage(conversation_agent_prompt.format(checkin_context=checkin_context, conversational_context=conversational_context)),
                HumanMessage("Please generate the conversation message based on my check-in and the conversation history.")
            ]
            
            # Stream the response chunk by chunk
            full_response = ""
            async for chunk in llm_service.chatbot_response(messages):
                if chunk:
                    # Send each chunk as plain text (no JSON metadata)
                    await websocket.send_text(chunk)
                    full_response += chunk
            
            # Store the conversation in Redis with sliding window approach
            redis_service.append_conversation(
                chat_id, 
                "Conversation continuation request", 
                full_response, 
                expire_seconds=14400
            )
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any message from client
                data = await websocket.receive_text()
                
                # Validate message format
                is_valid_msg, msg_error = validation_service.validate_message_format(data)
                if not is_valid_msg:
                    await websocket.send_text(f"Error: {msg_error}")
                    continue
                
                # Process message with agent service by getting the conversational context from the redis
                conversational_context = redis_service.get_conversation_context(chat_id)
                
                # Create messages for LLM with context
                messages = [
                    SystemMessage(f"You are a mental health support agent. Use this context: {conversational_context}"),
                    HumanMessage(data)
                ]
                
                # Stream the response chunk by chunk
                full_response = ""
                async for chunk in llm_service.chatbot_response(messages):
                    if chunk:
                        # Send each chunk as plain text (no JSON metadata)
                        await websocket.send_text(chunk)
                        full_response += chunk
                
                # Update Redis with new conversation context using sliding window
                redis_service.append_conversation(chat_id, data, full_response, expire_seconds=14400)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text("An error occurred while processing your message")
                break
                
    except WebSocketDisconnect:
        websocket_service.disconnect(chat_id)
        # Redis key will automatically expire after 4 hours, no need to manually delete
        logger.info(f"User {chat_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {chat_id}: {e}")
        websocket_service.disconnect(chat_id)
        # Redis key will automatically expire after 4 hours, no need to manually delete
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
