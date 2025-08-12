from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model for API responses"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    age: Optional[int] = None
    gender: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    age: Optional[int] = None
    gender: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator('username')
    @classmethod
    def get_display_username(cls, v, info):
        if hasattr(info.data.get('__object__'), 'display_username'):
            return info.data.get('__object__').display_username
        return v

    model_config = ConfigDict(from_attributes=True)

class SignupResponse(BaseModel):    
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None

# Check-in Models
class MorningCheckin(BaseModel):
    sleep_quality: str = Field(description="Quality of sleep (e.g., 'excellent', 'good', 'fair', 'poor')")
    body_sensation: str = Field(description="How the body feels (e.g., 'refreshed', 'tired', 'energized', 'achy')")
    energy_level: str = Field(description="Current energy level (e.g., 'high', 'medium', 'low', 'exhausted')")
    mental_state: str = Field(description="Mental state (e.g., 'clear', 'foggy', 'focused', 'scattered')")
    executive_task: str = Field(description="Ability to perform executive tasks (e.g., 'sharp', 'struggling', 'capable', 'overwhelmed')")

class EveningCheckin(BaseModel):
    emotion_category: str = Field(description="Primary emotion category (e.g., 'joy', 'sadness', 'anger', 'anxiety', 'contentment')")
    overwhelm_amount: str = Field(description="Level of overwhelm (e.g., 'none', 'slight', 'moderate', 'high', 'extreme')")
    emotion_in_moment: str = Field(description="Current emotion (e.g., 'calm', 'stressed', 'grateful', 'frustrated')")
    surroundings_impact: str = Field(description="Impact of surroundings (e.g., 'positive', 'negative', 'neutral', 'distracting')")
    meaningful_moments_quantity: str = Field(description="Number of meaningful moments (e.g., 'none', 'few', 'several', 'many')")

class CheckinResponse(BaseModel):
    message: str
    checkin_id: str
    checkin_type: str
    timestamp: str
    user_id: int