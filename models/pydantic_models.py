from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[dict] = None
