import logging
from typing import Dict, Any
from datetime import datetime, UTC
from models.database_models import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations related to check-ins"""
    
    @staticmethod
    async def get_patient_checkin_context(patient_id: str) -> Dict[str, Any]:
        """
        Get the most recent daily checkin for a specific patient from the dailycheckins collection.
        
        Args:
            patient_id: ID of the patient (ObjectId string)
            
        Returns:
            Dictionary containing the most recent daily checkin for the patient.
        """
        try:
            db = get_database()

            # Query for the most recent document from dailycheckins collection for the given patient
            checkin = await db.dailycheckins.find_one(
                {"patient": ObjectId(patient_id)},
                sort=[("createdAt", -1)]
            )

            if not checkin:
                logger.info(f"No daily checkins found for patient {patient_id}")
                return {
                    "patient_id": patient_id,
                    "checkin": None,
                    "found": False
                }

            # Convert ObjectId to string for JSON serialization
            checkin_data = dict(checkin)
            if "patient" in checkin_data:
                checkin_data["patient"] = str(checkin_data["patient"])

            # Format executive tasks for display
            executive_tasks = checkin_data.get('executiveTasks', 'Not specified')
            if isinstance(executive_tasks, list):
                executive_tasks_str = ', '.join(executive_tasks) if executive_tasks else 'Not specified'
            else:
                executive_tasks_str = executive_tasks if executive_tasks else 'Not specified'

            # Format check-in date
            checkin_date = checkin_data.get('createdAt', 'Not specified')

            # Create context string based on checkin type
            if checkin_data.get('type') == 'Morning':
                context_string = (
                    "Morning Check-in Summary:\n"
                    f"- Sleep Quality: {checkin_data.get('sleepQuality', 'Not specified')}\n"
                    f"- Body Sensation: {checkin_data.get('bodySensation', 'Not specified')}\n"
                    f"- Energy Level: {checkin_data.get('energyLevel', 'Not specified')}\n"
                    f"- Mental State: {checkin_data.get('mentalState', 'Not specified')}\n"
                    f"- Executive Tasks: {executive_tasks_str}\n"
                    f"- Total Points: {checkin_data.get('totalPoints', 'Not specified')}\n"
                    f"- Risk Level: {checkin_data.get('riskLevel', 'Not specified')}\n"
                    f"- Message: {checkin_data.get('message', 'No message')}\n"
                    f"- Check-in Date: {checkin_date}"
                )
            else:
                context_string = (
                    "Evening Check-in Summary:\n"
                    f"- Emotion Category: {checkin_data.get('emotionCategory', 'Not specified')}\n"
                    f"- Overwhelm Amount: {checkin_data.get('overwhelmAmount', 'Not specified')}\n"
                    f"- Emotion in Moment: {checkin_data.get('emotionInMoment', 'Not specified')}\n"
                    f"- Surroundings Impact: {checkin_data.get('surroundingsImpact', 'Not specified')}\n"
                    f"- Social Engagement Level: {checkin_data.get('socialEngagementLevel', 'Not specified')}\n"
                    f"- Meaningful Moments Quantity: {checkin_data.get('meaningfulMomentsQuantity', 'Not specified')}\n"
                    f"- Executive Tasks: {executive_tasks_str}\n"
                    f"- Total Points: {checkin_data.get('totalPoints', 'Not specified')}\n"
                    f"- Risk Level: {checkin_data.get('riskLevel', 'Not specified')}\n"
                    f"- Message: {checkin_data.get('message', 'No message')}\n"
                    f"- Check-in Date: {checkin_date}"
                )

            logger.info(
                f"Retrieved most recent daily checkin for patient {patient_id} and created context string"
            )

            return {
                "patient_id": patient_id,
                "document_id": str(checkin_data["_id"]),  # Return the document ID for updating
                "context_string": context_string,
                "checkin_type": checkin_data.get('type', 'Unknown'),
                "found": True
            }

        except Exception as e:
            logger.error(f"Error retrieving daily checkin for patient {patient_id}: {e}")
            return {
                "patient_id": patient_id,
                "checkin": None,
                "found": False,
                "error": str(e)
            }
    
    @staticmethod
    async def add_checkin_summary(document_id: str, summary_message: str) -> Dict[str, Any]:
        """
        Update the message field of a specific checkin document with the generated summary
        
        Args:
            document_id: The MongoDB document ID (ObjectId string)
            summary_message: The generated summary message to store
            
        Returns:
            Dictionary containing the update result
        """
        try:
            db = get_database()
            
            # Update the document with the new message
            result = await db.dailycheckins.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "message": summary_message,
                        "updatedAt": datetime.now(UTC)
                    }
                }
            )
            
            if result.modified_count == 1:
                logger.info(f"Successfully updated message for document {document_id}")
                return {
                    "document_id": document_id,
                    "success": True,
                    "message": "Message updated successfully"
                }
            else:
                logger.warning(f"No document found with ID {document_id} or no changes made")
            return {
                    "document_id": document_id,
                    "success": False,
                    "message": "Document not found or no changes made"
            }
            
        except Exception as e:
            logger.error(f"Error updating message for document {document_id}: {e}")
            return {
                "document_id": document_id,
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    @staticmethod
    async def save_chat_message(
        patient_id: str,
        query: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Save a chat message (query and response) to the chats collection
        
        Args:
            patient_id: ID of the patient (ObjectId string)
            query: User's message/question
            response: AI assistant's response
            
        Returns:
            Dictionary containing the saved chat data
        """
        try:
            db = get_database()
            
            # Create chat document
            chat_document = {
                "patient": ObjectId(patient_id),
                "query": query,
                "response": response,
                "createdAt": datetime.now(UTC),
                "updatedAt": datetime.now(UTC)
            }
            
            # Insert the document
            result = await db.chats.insert_one(chat_document)
            
            logger.info(f"Successfully saved chat message for patient {patient_id}")
            
            return {
                "chat_id": str(result.inserted_id),
                "patient_id": patient_id,
                "query": query,
                "response": response,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error saving chat message for patient {patient_id}: {e}")
            return {
                "patient_id": patient_id,
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def get_patient_recent_chats(patient_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get the recent chat conversations for a specific patient and format them for context
        
        Args:
            patient_id: ID of the patient (ObjectId string)
            limit: Maximum number of chat messages to return (default: 20)
            
        Returns:
            Dictionary containing the recent chat conversations and formatted context string
        """
        try:
            db = get_database()
            
            # Query recent chat messages for the patient, sorted by creation date (newest first)
            chats = await db.chats.find(
                {"patient": ObjectId(patient_id)}
            ).sort("createdAt", -1).limit(limit).to_list(length=None)
            
            # Convert ObjectIds to strings for JSON serialization
            chat_list = []
            for chat in chats:
                chat_data = dict(chat)
                # Convert ObjectIds to strings
                if "_id" in chat_data:
                    chat_data["_id"] = str(chat_data["_id"])
                if "patient" in chat_data:
                    chat_data["patient"] = str(chat_data["patient"])
                chat_list.append(chat_data)
            
            # Build conversational context string
            conversational_context = ""
            if chat_list:
                # Use last 15 conversations for context
                recent_chats = chat_list[:15]
                chat_strings = []
                for chat in recent_chats:
                    chat_strings.append(f"User: {chat['query']}\nAssistant: {chat['response']}")
                conversational_context = "\n\n".join(chat_strings)
            else:
                conversational_context = "This is the beginning of our conversation."
            
            logger.info(f"Retrieved {len(chat_list)} recent chats for patient {patient_id}")
            
            return {
                "patient_id": patient_id,
                "chats": chat_list,
                "conversational_context": conversational_context,
                "total_count": len(chat_list),
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error retrieving recent chats for patient {patient_id}: {e}")
            return {
                "patient_id": patient_id,
                "chats": [],
                "conversational_context": "This is the beginning of our conversation.",
                "total_count": 0,
                "limit": limit,
                "error": str(e)
            }


if __name__ == "__main__":
    import asyncio
    from models.database_models import connect_to_mongo
    
    async def test_connection():
        await connect_to_mongo()
        print("MongoDB connection successful!")
        
        # Test the get_patient_daily_checkins function
        test_patient_id = "6899521238bcd98456d965e0"  # Using the actual patient ID from your database
        result = await DatabaseService.get_patient_checkin_context(test_patient_id)
        print(f"Test result for patient {test_patient_id}:")
        print(f"Checkin found: {result['found']}")
        if result['found'] and result['context_string']:
            print(f"Checkin type: {result['checkin_type']}")
            print(f"Document ID: {result['document_id']}")
            print("Context string for summary generation:")
            print(result['context_string'])
            
            # Example: Update the message with a sample summary
            sample_summary = "Patient reported feeling tense and low energy during morning check-in. Risk level is high. Recommend focusing on self-care activities and stress management techniques."
            update_result = await DatabaseService.add_checkin_summary(result['document_id'], sample_summary)
            print(f"Update result: {update_result}")
        else:
            print("No checkins found for this patient")
    
    asyncio.run(test_connection())