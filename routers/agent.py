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
from services.auth_service import get_current_active_user, get_current_user_from_token
from services.websocket_service import WebSocketService
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
validation_service = ValidationService()
redis_service = RedisService()
llm_service = LLMService()

@router.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """WebSocket endpoint for mental health bot connection with JWT authentication"""
    
    try:
        # Validate chat ID
        is_valid_chat, chat_error = validation_service.validate_chat_id(chat_id)
        if not is_valid_chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=chat_error)
            return
        
        # Get database session
        db = next(get_db())
        
        # Authenticate user via JWT token from query parameters
        try:
            # Get token from query parameters
            token = websocket.query_params.get("token")
            logger.info(f"WebSocket connection attempt - Chat ID: {chat_id}, Token: {token[:20] if token else 'None'}...")
            
            if not token:
                logger.warning(f"Missing token for chat_id: {chat_id}")
                await websocket.accept()
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token parameter")
                return
            
            # Validate token and get current user
            logger.info(f"Validating token for chat_id: {chat_id}")
            current_user = await get_current_user_from_token(token, db)
            
            if not current_user or not current_user.is_active:
                logger.warning(f"Invalid or inactive user for chat_id: {chat_id}")
                await websocket.accept()
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or inactive user")
                return
            
            logger.info(f"User authenticated successfully - User ID: {current_user.id}, Email: {current_user.email}")
            
            # Accept the connection first
            await websocket.accept()
            
            # Store connection in websocket service
            await websocket_service.connect(websocket, chat_id, current_user)
            
        except Exception as auth_error:
            logger.error(f"Authentication error: {auth_error}")
            try:
                await websocket.accept()
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            except:
                pass
            return

        # Checking if we are talking about the morning or evening checkin
        morning_checking = False
        try:
            if chat_id.split('_')[2] == '1':
                # Means evening checkin
                morning_checking = False
            else:
                # Means morning checkin
                morning_checking = True
        except:
            morning_checking = True  # Default to morning if parsing fails

        # Getting the checkin context from the database
        logger.info("🔍 [SYSTEM] Retrieving checkin context from database...")
        checkin_context = DatabaseService.get_last_daily_checkin(db, current_user.id, morning_checking)
        logger.info(f"📊 [SYSTEM] Checkin context retrieved: {checkin_context}")
        
        # Handle case where no checkin context is available
        if not checkin_context:
            logger.warning(f"⚠️ [SYSTEM] No checkin context found for user {current_user.id}, using default context")
            checkin_context = {
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "age": current_user.age,
                "gender": current_user.gender,
                "default_message": "No recent check-in data available. Let's start fresh."
            }
        
        # Convert checkin context to readable string format
        def dict_to_string(data):
            if not data:
                return "No data available"
            return ", ".join([f"{key}: {value}" for key, value in data.items()])
        
        checkin_context_string = dict_to_string(checkin_context)
        
        # Check if chat_id exists in Redis
        chat_exists = redis_service.key_exists(chat_id)
        logger.info(f"🔍 [SYSTEM] Chat analysis - ID: {chat_id}, Morning: {morning_checking}, Redis exists: {chat_exists}")
        logger.info(f"📋 [SYSTEM] Checkin context: {checkin_context_string}")
        
        if not chat_exists:
            # GREETING AGENT - First time user connection
            logger.info("🤖 [GREETING AGENT] Starting new conversation")
            try:
                logger.info(f"📝 [GREETING AGENT] Formatting prompt with context: {checkin_context_string}")
                
                # Use string replacement instead of .format() to avoid conflicts
                formatted_prompt = greeting_agent_prompt.replace("{{checkin_context}}", checkin_context_string)
                
                messages = [
                    SystemMessage(formatted_prompt),
                    HumanMessage("Please generate the greeting based on my check-in.")
                ]
                logger.info("✅ [GREETING AGENT] Prompt formatted successfully")
            except Exception as format_error:
                logger.error(f"❌ [GREETING AGENT] Error formatting prompt: {format_error}")
                # Fallback to a simple greeting
                messages = [
                    SystemMessage(f"You are Kay, a mental health support agent. Greet the user {current_user.first_name} warmly and ask how they are feeling today."),
                    HumanMessage("Please generate a warm greeting.")
                ]
                logger.info("🔄 [GREETING AGENT] Using fallback prompt")
            
            # Get response from LLM
            full_response = ""
            try:
                logger.info("🔄 [GREETING AGENT] Generating response from LLM...")
                async for chunk in llm_service.chatbot_response(messages):
                    if chunk:
                        full_response = chunk  # Now we get the complete response in one chunk
                        break  # Exit after first chunk since it contains the full response
                
                # Send complete response
                if websocket.client_state.value == 1:  # Check if WebSocket is still open
                    await websocket.send_text(full_response)
                    logger.info(f"✅ [GREETING AGENT] Response sent successfully ({len(full_response)} chars)")
                    logger.info(f"📤 [GREETING AGENT] Response preview: {full_response[:100]}...")
                else:
                    logger.warning("⚠️ [GREETING AGENT] WebSocket closed, cannot send response")
                    return
            except Exception as stream_error:
                logger.error(f"❌ [GREETING AGENT] Error getting LLM response: {stream_error}")
                error_message = "I'm having trouble generating a response right now. Please try again."
                await websocket.send_text(error_message)
                full_response = error_message
                logger.info("🔄 [GREETING AGENT] Sent error fallback message")
            
            # Store the greeting in Redis with sliding window approach
            redis_service.append_conversation(
                chat_id, 
                "Initial greeting request", 
                full_response, 
                expire_seconds=14400
            )
            logger.info("💾 [GREETING AGENT] Conversation stored in Redis")
        else:
            # CONVERSATION AGENT - Continuing existing conversation
            logger.info("🤖 [CONVERSATION AGENT] Continuing existing conversation")
            conversational_context = redis_service.get_conversation_context(chat_id)
            logger.info(f"📚 [CONVERSATION AGENT] Retrieved context from Redis: {conversational_context[:100] if conversational_context else 'None'}...")
            
            # Handle empty conversation context
            if not conversational_context:
                logger.info("⚠️ [CONVERSATION AGENT] Empty context, treating as new conversation")
                conversational_context = "This is the beginning of our conversation."
            
            try:
                # Convert contexts to readable string format
                checkin_string = dict_to_string(checkin_context)
                conversation_string = str(conversational_context) if conversational_context else "No conversation context available"
                logger.info(f"📝 [CONVERSATION AGENT] Formatting prompt with checkin: {checkin_string}")
                logger.info(f"💬 [CONVERSATION AGENT] Conversation context: {conversation_string[:100]}...")
                
                # Use string replacement instead of .format() to avoid conflicts
                formatted_prompt = conversation_agent_prompt.replace("{{checkin_context}}", checkin_string)
                formatted_prompt = formatted_prompt.replace("{{conversation_history}}", conversation_string)
                
                messages = [
                    SystemMessage(formatted_prompt),
                    HumanMessage("Please generate the conversation message based on my check-in and the conversation history.")
                ]
                logger.info("✅ [CONVERSATION AGENT] Prompt formatted successfully")
            except Exception as format_error:
                logger.error(f"❌ [CONVERSATION AGENT] Error formatting prompt: {format_error}")
                # Fallback to a simple conversation prompt
                messages = [
                    SystemMessage(f"You are Kay, a mental health support agent. Continue the conversation with {current_user.first_name} based on the context: {conversational_context}"),
                    HumanMessage("Please continue the conversation naturally.")
                ]
                logger.info("🔄 [CONVERSATION AGENT] Using fallback prompt")
            
            # Get response from LLM
            full_response = ""
            try:
                logger.info("🔄 [CONVERSATION AGENT] Generating response from LLM...")
                async for chunk in llm_service.chatbot_response(messages):
                    if chunk:
                        full_response = chunk  # Now we get the complete response in one chunk
                        break  # Exit after first chunk since it contains the full response
                
                # Send complete response
                if websocket.client_state.value == 1:  # Check if WebSocket is still open
                    await websocket.send_text(full_response)
                    logger.info(f"✅ [CONVERSATION AGENT] Response sent successfully ({len(full_response)} chars)")
                    logger.info(f"📤 [CONVERSATION AGENT] Response preview: {full_response[:100]}...")
                else:
                    logger.warning("⚠️ [CONVERSATION AGENT] WebSocket closed, cannot send response")
                    return
            except Exception as stream_error:
                logger.error(f"❌ [CONVERSATION AGENT] Error getting LLM response: {stream_error}")
                error_message = "I'm having trouble generating a response right now. Please try again."
                await websocket.send_text(error_message)
                full_response = error_message
                logger.info("🔄 [CONVERSATION AGENT] Sent error fallback message")
            
            # Store the conversation in Redis with sliding window approach
            redis_service.append_conversation(
                chat_id, 
                "Conversation continuation request", 
                full_response, 
                expire_seconds=14400
            )
            logger.info("💾 [CONVERSATION AGENT] Conversation stored in Redis")
        
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
                
                # USER MESSAGE PROCESSING - Handle ongoing conversation
                logger.info("💬 [USER MESSAGE] Processing user input")
                conversational_context = redis_service.get_conversation_context(chat_id)
                
                # Handle empty conversation context
                if not conversational_context:
                    conversational_context = "This is the beginning of our conversation."
                    logger.info("⚠️ [USER MESSAGE] Empty context, treating as new conversation")
                
                # Create messages for LLM with context
                try:
                    # Convert conversational context to readable string format
                    context_string = str(conversational_context) if conversational_context else "No context available"
                    logger.info(f"📝 [USER MESSAGE] Creating LLM messages with context: {context_string[:100]}...")
                    
                    messages = [
                        SystemMessage(f"You are a mental health support agent. Use this context: {context_string}"),
                        HumanMessage(data)
                    ]
                    logger.info("✅ [USER MESSAGE] Messages created successfully")
                except Exception as msg_error:
                    logger.error(f"❌ [USER MESSAGE] Error creating messages: {msg_error}")
                    # Fallback to simple message
                    messages = [
                        SystemMessage("You are a mental health support agent. Be supportive and helpful."),
                        HumanMessage(data)
                    ]
                    logger.info("🔄 [USER MESSAGE] Using fallback messages")
                
                # Get response from LLM
                full_response = ""
                try:
                    logger.info("🔄 [USER MESSAGE] Generating response from LLM...")
                    async for chunk in llm_service.chatbot_response(messages):
                        if chunk:
                            full_response = chunk  # Now we get the complete response in one chunk
                            break  # Exit after first chunk since it contains the full response
                    
                    # Send complete response
                    if websocket.client_state.value == 1:  # Check if WebSocket is still open
                        await websocket.send_text(full_response)
                        logger.info(f"✅ [USER MESSAGE] Response sent successfully ({len(full_response)} chars)")
                        logger.info(f"📤 [USER MESSAGE] Response preview: {full_response[:100]}...")
                    else:
                        logger.warning("⚠️ [USER MESSAGE] WebSocket closed, cannot send response")
                        return
                except Exception as stream_error:
                    logger.error(f"❌ [USER MESSAGE] Error getting LLM response: {stream_error}")
                    error_message = "I'm having trouble generating a response right now. Please try again."
                    await websocket.send_text(error_message)
                    full_response = error_message
                    logger.info("🔄 [USER MESSAGE] Sent error fallback message")
                
                # Update Redis with new conversation context using sliding window
                redis_service.append_conversation(chat_id, data, full_response, expire_seconds=14400)
                logger.info("💾 [USER MESSAGE] Conversation updated in Redis")
                
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



# @router.post("/send-message")
# async def send_message_to_user(
#     chat_id: str,
#     message: str,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Send a message to a specific user via WebSocket (admin/provider only)"""
    
#     # Validate chat ID
#     is_valid_chat, chat_error = validation_service.validate_chat_id(chat_id)
#     if not is_valid_chat:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=chat_error
#         )
    
#     # Validate message format
#     is_valid_msg, msg_error = validation_service.validate_message_format(message)
#     if not is_valid_msg:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=msg_error
#         )
    
#     # Check user permissions
#     has_permission, perm_error = validation_service.validate_user_permissions(current_user, "provider")
#     if not has_permission:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=perm_error
#         )
    
#     # Check if user is connected
#     if not websocket_service.is_connected(chat_id):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User is not currently connected"
#         )
    
#     # Send message
#     admin_message = {
#         "type": "admin_message",
#         "content": message,
#         "from_user": current_user.id,
#         "from_user_name": f"{current_user.first_name} {current_user.last_name}",
#         "timestamp": datetime.now(UTC).isoformat()
#     }
    
#     success = await websocket_service.send_json_message(admin_message, chat_id)
    
#     if success:
#         return validation_service.create_success_response(
#             "message_sent",
#             "Message sent successfully",
#             chat_id=chat_id
#         )
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to send message"
#         )
