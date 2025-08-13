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
        self.chat_openai = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o", temperature=0.7,timeout=None, max_retries=2)
        self.logger = logging.getLogger(__name__)

    async def chatbot_response(self, messages):
        """
        Streams the response from the LLM as an async generator of text chunks.
        """
        try:
            stream = self.chat_openai.stream(messages)
            for chunk in stream:
                # Each chunk is a ChatMessage; yield its content
                if chunk and chunk.content:
                    yield chunk.content
        except Exception as e:
            self.logger.error(f"Error in chatbot_response: {e}")
            yield f"Error: {str(e)}"
        

    # def get_response_with_retry(self, messages, keys_to_check):
    #     retries = 3
    #     for attempt in range(retries):
    #         try:
    #             response = self.chat_openai.invoke(messages)
    #             response = response.content

    #             # Only check for missing keys, allow values to be None or null
    #             missing_keys = [key for key in keys_to_check if key not in response]
    #             if not missing_keys:
    #                 return response
    #             else:
    #                 raise ValueError(f"Missing keys in response: {missing_keys}")
    #         except Exception as e:
    #             self.logger.error(f"Error retrieving response: {e}. Attempt {attempt + 1} of {retries}.")
    #     return {}

  

    # async def generate_transcription_summary(self, transcription: str):
    #     """
    #     Generates a summary of the transcription using LangChain and GPT-4o-mini.
    #     """
    #     try:
    #         summary_prompt = """
    #         You are an expert at analyzing call transcriptions and creating concise, professional summaries.
            
    #         Please analyze the following call transcription and provide a comprehensive summary that includes:
            
    #         1. Call Purpose: What was the main objective of this call?
    #         2. Key Points Discussed: What were the main topics or points covered?
    #         3. Outcome: What was the result or conclusion of the call?
    #         4. Action Items: Are there any follow-up actions needed?
    #         5. Sentiment: What was the overall tone and sentiment of the conversation?
            
    #         Transcription:
    #         {transcription}
            
    #         IMPORTANT: Please provide your analysis in plain text format without any markdown symbols (no ###, **, '', etc.). Use proper numbering (1, 2, 3, etc.) and clear section breaks with line spacing. Make it easy to read and well-structured but without any markdown formatting.
    #         """
            
    #         messages = [
    #             SystemMessage(summary_prompt.format(transcription=transcription)),
    #             HumanMessage("Please provide a comprehensive summary of this call transcription.")
    #         ]
            
    #         # Use the existing retry mechanism
    #         summary = self.get_response_with_retry(messages, [])
            
    #         if summary:
    #             self.logger.info(f"Successfully generated summary for transcription of length {len(transcription)}")
    #             return summary
    #         else:
    #             self.logger.error("Failed to generate summary - empty response")
    #             return None
                
    #     except Exception as e:
    #         self.logger.error(f"Error generating transcription summary: {str(e)}")
    #         import traceback
    #         self.logger.error(f"Full traceback: {traceback.format_exc()}")
    #         return None


# if __name__ == "__main__":
#     llm_service = LLMService()
#     transcript = """
# Hey, so listen basically there are a lot of things that I would like to inquire about. The very first thing is that I just want to 
# figure out that do you have any kind of products which are related to some oily skin and to be more precise that it would be better
# that if you can provide me some of the products that are better suited for like dusky skin tone because I have a dusky skin tone so
# I want that such kind of product and also make sure that in your store also try to include that the medicines which do not have any
# kind of reported skin allergies or something. So I just want this thing to be considered in the products which you are going to 
# show me right now. So kindly make sure about this thing.
# """
#     # Escape curly braces in transcript to prevent format errors
#     safe_transcript = transcript.replace("{", "{{").replace("}", "}}")
#     messages = [
#         SystemMessage(call_analysis_prompt.format(transcript=safe_transcript)),
#         HumanMessage("Extract the key information from the transcript")
#     ]
#     response = llm_service.get_response_with_retry(messages, ["contact_name", "contact_email", "contact_number", "call_objective"])