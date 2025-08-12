from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
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


# Database dependency
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()