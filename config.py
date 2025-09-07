from pydantic_settings import BaseSettings
from typing import List
import random
from rich import print

class Settings(BaseSettings):
    """Application settings"""
    
    # API settings
    api_title: str = "Mental Health Bot API"
    api_description: str = "A FastAPI application for mental health support and counseling"
    api_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # OpenAI settings
    openai_api_key: str = ""

    # MongoDB settings
    mongodb_url: str
    mongodb_database: str
    
    # API Authentication settings
    server_api_key: str = ""  # Secret key for Node.js server authentication 

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create settings instance
settings = Settings()


if __name__ == "__main__":
    for i in range(10):
        print(settings.get_random_voice())