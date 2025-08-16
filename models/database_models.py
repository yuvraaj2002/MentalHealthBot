from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, UTC
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Database configuration
DATABASE_URL = settings.postgresql_db

# Create engine with connection pool management for Neon serverless
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,          # Ensures dead connections are removed before use
    pool_recycle=1800,           # Recycles connections older than 30 minutes
    pool_size=5,                 # Number of connections to maintain in pool
    max_overflow=10,             # Additional connections for traffic spikes
    connect_args={
        "connect_timeout": 10,   # Connection timeout in seconds
        "application_name": "mental_health_bot_app"  # Help identify connections in logs
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class User(Base):
    """User table for authentication - handles both regular users and providers"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    age = Column(Integer, nullable=True)
    gender = Column(Integer, nullable=True)  # 0: Male, 1: Female, 2: Third gender
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

class Conversation(Base):
    """Conversation table for storing conversation history"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversations = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

class Checkin(Base):
    """Daily check-in table for mental health tracking"""
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_type = Column(String(20), nullable=False)  # "morning" or "evening"
    
    # Morning check-in fields
    sleep_quality = Column(String(100), nullable=True)
    body_sensation = Column(String(100), nullable=True)
    energy_level = Column(String(100), nullable=True)
    mental_state = Column(String(100), nullable=True)
    executive_task = Column(String(100), nullable=True)
    
    # Evening check-in fields
    emotion_category = Column(String(100), nullable=True)
    overwhelm_amount = Column(String(100), nullable=True)
    emotion_in_moment = Column(String(100), nullable=True)
    surroundings_impact = Column(String(100), nullable=True)
    meaningful_moments_quantity = Column(String(100), nullable=True)
    
    # Timestamps
    checkin_time = Column(DateTime, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

class ChatSummary(Base):
    """Chat summary table for storing conversation summaries"""
    __tablename__ = "chat_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(String(255), nullable=False)  # Store the chat_id string
    summary = Column(Text, nullable=False)  # Store the generated summary
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

# Create indexes for performance optimization
Index('idx_checkins_user_type_time', Checkin.user_id, Checkin.checkin_type, Checkin.checkin_time)
Index('idx_checkins_user_time', Checkin.user_id, Checkin.checkin_time)
Index('idx_users_id', User.id)
Index('idx_chat_summaries_user_chat', ChatSummary.user_id, ChatSummary.chat_id)
Index('idx_chat_summaries_chat_id', ChatSummary.chat_id)

# Database dependency
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()