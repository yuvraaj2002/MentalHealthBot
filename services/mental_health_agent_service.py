import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models.database_models import User, Conversation

logger = logging.getLogger(__name__)

class MentalHealthAgentService:
    """Service class for mental health bot agent functionality"""
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Crisis keywords that require immediate attention
        self.crisis_keywords = [
            "suicide", "kill myself", "want to die", "end it all",
            "harm myself", "self harm", "cut myself", "overdose",
            "no reason to live", "better off dead", "give up"
        ]
        
        # Mood tracking keywords
        self.mood_keywords = {
            "positive": ["happy", "good", "great", "excellent", "wonderful", "amazing"],
            "neutral": ["okay", "fine", "alright", "normal", "stable"],
            "negative": ["sad", "depressed", "anxious", "worried", "stressed", "angry", "frustrated"]
        }
    
    async def process_user_message(self, content: str, user_id: str, db: Session) -> Dict[str, Any]:
        """Process user message and generate appropriate response"""
        
        try:
            # Check for crisis indicators
            if self._detect_crisis(content):
                return self._generate_crisis_response()
            
            # Analyze mood
            mood_analysis = self._analyze_mood(content)
            
            # Generate contextual response
            response = self._generate_contextual_response(content, mood_analysis)
            
            # Store conversation
            self._store_conversation(user_id, "user", content, mood_analysis)
            self._store_conversation(user_id, "bot", response, mood_analysis)
            
            # Save to database
            await self._save_conversation_to_db(user_id, content, response, db)
            
            return {
                "type": "bot_response",
                "content": response,
                "mood": mood_analysis,
                "timestamp": datetime.now(UTC).isoformat(),
                "requires_followup": self._requires_followup(content, mood_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {
                "type": "error",
                "content": "I'm having trouble processing your message right now. Please try again.",
                "timestamp": datetime.now(UTC).isoformat()
            }
    
    def _detect_crisis(self, content: str) -> bool:
        """Detect crisis indicators in user message"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.crisis_keywords)
    
    def _generate_crisis_response(self) -> Dict[str, Any]:
        """Generate crisis response with appropriate resources"""
        return {
            "type": "crisis_response",
            "content": "I'm very concerned about what you're saying. If you're in crisis, please know that you matter and help is available. Please call the National Suicide Prevention Lifeline at 988 or text HOME to 741741. You can also call 911 or go to your nearest emergency room. You're not alone, and there are people who want to help you.",
            "priority": "high",
            "requires_immediate_attention": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    def _analyze_mood(self, content: str) -> Dict[str, Any]:
        """Analyze the mood of the user's message"""
        content_lower = content.lower()
        
        detected_moods = []
        for mood_type, keywords in self.mood_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_moods.append(mood_type)
        
        # Default to neutral if no mood detected
        if not detected_moods:
            detected_moods = ["neutral"]
        
        return {
            "primary_mood": detected_moods[0],
            "detected_moods": detected_moods,
            "confidence": len(detected_moods) / len(self.mood_keywords),
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    def _generate_contextual_response(self, content: str, mood_analysis: Dict[str, Any]) -> str:
        """Generate contextual response based on message content and mood"""
        
        content_lower = content.lower()
        primary_mood = mood_analysis.get("primary_mood", "neutral")
        
        # Greeting responses
        if any(word in content_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "Hello! I'm here to support you today. How are you feeling?"
        
        # Mood-specific responses
        if primary_mood == "negative":
            if any(word in content_lower for word in ["sad", "depressed", "down"]):
                return "I'm sorry you're feeling this way. It's completely okay to not be okay. Would you like to talk about what's on your mind? I'm here to listen."
            elif any(word in content_lower for word in ["anxious", "worried", "stress"]):
                return "Anxiety can be really challenging. Let's take a moment to breathe together. What's causing you to feel this way? Sometimes talking about it can help."
            elif any(word in content_lower for word in ["angry", "frustrated", "mad"]):
                return "I can sense that you're feeling frustrated. That's a valid emotion. Would you like to talk about what happened? I'm here to support you."
        
        elif primary_mood == "positive":
            return "I'm glad you're feeling good today! It's wonderful to hear positive moments. Is there anything specific you'd like to talk about or work on?"
        
        # Support-seeking responses
        if any(word in content_lower for word in ["help", "support", "need help"]):
            return "I'm here to help and support you. You're not alone in this. What would be most helpful right now? I can listen, provide resources, or just be here with you."
        
        # General supportive response
        return "Thank you for sharing that with me. I'm listening and here to support you. Can you tell me more about how you're feeling or what's on your mind?"
    
    def _requires_followup(self, content: str, mood_analysis: Dict[str, Any]) -> bool:
        """Determine if the message requires follow-up attention"""
        primary_mood = mood_analysis.get("primary_mood", "neutral")
        
        # High priority for negative moods
        if primary_mood == "negative":
            return True
        
        # Check for specific concerning phrases
        concerning_phrases = [
            "don't know what to do", "can't handle this", "overwhelmed",
            "alone", "lonely", "no one understands", "tired of feeling"
        ]
        
        content_lower = content.lower()
        return any(phrase in content_lower for phrase in concerning_phrases)
    
    def _store_conversation(self, user_id: str, sender: str, content: str, mood_analysis: Optional[Dict[str, Any]] = None):
        """Store conversation in memory"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        conversation_entry = {
            "sender": sender,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat(),
            "mood": mood_analysis
        }
        
        self.conversation_history[user_id].append(conversation_entry)
        
        # Keep only last 50 messages to prevent memory issues
        if len(self.conversation_history[user_id]) > 50:
            self.conversation_history[user_id] = self.conversation_history[user_id][-50:]
    
    async def _save_conversation_to_db(self, user_id: str, user_message: str, bot_response: str, db: Session):
        """Save conversation to database"""
        try:
            conversation = Conversation(
                user_id=user_id,
                conversations=json.dumps({
                    "user_message": user_message,
                    "bot_response": bot_response,
                    "timestamp": datetime.now(UTC).isoformat()
                })
            )
            db.add(conversation)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save conversation to database: {e}")
            db.rollback()
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        return self.conversation_history.get(user_id, [])
    
    def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total_conversations = sum(len(conv) for conv in self.conversation_history.values())
        active_users = len(self.conversation_history)
        
        return {
            "total_conversations": total_conversations,
            "active_users": active_users,
            "conversation_history_size": len(self.conversation_history),
            "timestamp": datetime.now(UTC).isoformat()
        }
