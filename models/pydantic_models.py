from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class ChatSummaryResponse(BaseModel):
    patient_id: str
    document_id: str
    summary: str
    update_success: bool

class KayBotPayload(BaseModel):
    age: str
    gender: str
    name: str
    patient_id: str
    message: str