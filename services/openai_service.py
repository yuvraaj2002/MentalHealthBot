from config import settings
import os
import time
import inspect
from rich import print
import logging
from prompt_registry import *
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class LLMService:
    def __init__(self):
        self.chat_openai = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o", temperature=0.8,timeout=None, max_retries=2)
        self.logger = logging.getLogger(__name__)


    async def get_chat_summary(self, context_string: str):
        """
        Generates a summary of the checkin data using LangChain and GPT-4o-mini.
        """
        try:
            # Use string replacement to avoid format conflicts
            formatted_prompt = summary_prompt.replace("{{context_string}}", context_string)
            
            messages = [
                SystemMessage(formatted_prompt),
                HumanMessage("Please provide a summary of the checkin data.")
            ]
            response = await self.chat_openai.ainvoke(messages)
            return response.content
        except Exception as e:
            self.logger.error(f"Error generating chat summary: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    async def generate_kay_response(
        self,
        user_message: str,
        patient_name: str,
        patient_age: str,
        patient_gender: str,
        checkin_context: str,
        conversational_context: str
    ) -> str:
        """
        Generate a response from Kay bot using patient context and conversation history
        """
        try:
            # Create checkin context for the prompt
            complete_checkin_context_data = {
                "first_name": patient_name,
                "age": int(patient_age) if patient_age.isdigit() else 25,
                "gender": patient_gender,
                "checkin_data": checkin_context
            }
            
            # Convert to string format
            checkin_string = f"Name: {complete_checkin_context_data['first_name']}, Age: {complete_checkin_context_data['age']}, Gender: {complete_checkin_context_data['gender']}\nCheck-in Data: {complete_checkin_context_data['checkin_data']}"
            
            # Use conversation agent prompt for ongoing conversations
            formatted_prompt = kay_bot_prompt.replace("{{checkin_context}}", checkin_string)
            formatted_prompt = formatted_prompt.replace("{{conversation_history}}", conversational_context)
            
            messages = [
                SystemMessage(formatted_prompt),
                HumanMessage(user_message)
            ]
            
            response = await self.chat_openai.ainvoke(messages)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generating Kay response: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return "I'm sorry, I'm having trouble responding right now. Please try again."
        
    