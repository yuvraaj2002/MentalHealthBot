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

from models.database_models import get_db, get_connection_pool_stats
from services.db_service import DatabaseService
from services.openai_service import LLMService
from services.api_auth_service import get_verified_api_key, APIAuthService
from config import settings
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_registry import *
from models.pydantic_models import KayBotPayload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Mental Health Agent"])

# Initialize services
llm_service = LLMService()

@router.post("/kay-bot")
async def generate_response(payload: KayBotPayload, api_key: str = Depends(get_verified_api_key)):
    """Generate a response from the Kay bot using patient context and chat history"""
    
    try:
        # Get patient's recent chat history (last 20 conversations)
        chat_history_result = await DatabaseService.get_patient_recent_chats(payload.patient_id, limit=20)
        conversational_context = chat_history_result.get('conversational_context', "This is the beginning of our conversation.")
        logger.info(f"[KAY-BOT] Retrieved {chat_history_result['total_count']} recent chats for patient {payload.patient_id}")
        
        # Get patient's checkin context
        checkin_result = await DatabaseService.get_patient_checkin_context(payload.patient_id)
        logger.info(f"[KAY-BOT] Checkin context found: {checkin_result['found']}")
        registered_checkin_context = ""
        if checkin_result['found']:
            registered_checkin_context = checkin_result['context_string']
        else:
            # Create basic context from payload if no checkin data
            registered_checkin_context = f"Patient: {payload.name}, Age: {payload.age}, Gender: {payload.gender}"
        
        # Generate response using LLM service
        response = await llm_service.generate_kay_response(
            user_message=payload.message,
            patient_name=payload.name,
            patient_age=payload.age,
            patient_gender=payload.gender,
            checkin_context=registered_checkin_context,
            conversational_context=conversational_context
        )
        
        # Save the conversation to database
        save_result = await DatabaseService.save_chat_message(
            patient_id=payload.patient_id,
            query=payload.message,
            response=response
        )
        
        if not save_result['success']:
            logger.error(f"Failed to save chat message for patient {payload.patient_id}")
        
        logger.info(f"[KAY-BOT] Generated response for patient {payload.patient_id}")
        
        return {
            "response": response,
            "patient_id": payload.patient_id,
            "chat_saved": save_result['success'],
            "chat_id": save_result.get('chat_id', None)
        }
        
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "mental-health-agent",
        "api_auth": APIAuthService.get_api_key_info()
    }

@router.get("/health/db")
async def database_health_check():
    """Database health check with connection pool stats"""
    try:
        # Get connection pool statistics
        pool_stats = await get_connection_pool_stats()
        
        # Test database connectivity
        db = await get_db()
        await db.command("ping")
        
        return {
            "status": "healthy",
            "database": "connected",
            "connection_pool": pool_stats,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }


# Endpoint for creating the summary against registered checkin id
@router.get("/chat/summary/{patient_id}")
async def get_chat_summary(patient_id: str, api_key: str = Depends(get_verified_api_key)):
    """Get the summary of the chat session and update the checkin document"""

    try:
        # Getting the checkin context and document ID
        checkin_result = await DatabaseService.get_patient_checkin_context(patient_id)
        logger.info(f"[SYSTEM] Checkin result: {checkin_result}")

        if not checkin_result['found']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No checkin found for patient {patient_id}"
            )

        # Getting the summary of the chat session using the context string
        context_string = checkin_result['context_string']
        summary = await llm_service.get_chat_summary(context_string)
        logger.info(f"[SYSTEM] Generated summary: {summary}")

        # Update the checkin document with the generated summary
        document_id = checkin_result['document_id']
        update_result = await DatabaseService.add_checkin_summary(document_id, summary)
        logger.info(f"[SYSTEM] Update result: {update_result}")

        if not update_result['success']:
            logger.error(f"Failed to add checkin summary for document_id: {document_id}")
            # Continue with the response even if updating fails

        return {
            "patient_id": patient_id,
            "document_id": document_id,
            "summary": summary,
            "update_success": update_result['success']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

@router.get("/auth/test")
async def test_authentication(api_key: str = Depends(get_verified_api_key)):
    """Test endpoint to verify API key authentication is working"""
    return {
        "status": "success",
        "message": "API key authentication successful",
        "timestamp": datetime.now(UTC).isoformat()
    }














