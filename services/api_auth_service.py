"""
API Key Authentication Service for FastAPI
Handles authentication between Node.js server and FastAPI server using secret keys
"""

import logging
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

logger = logging.getLogger(__name__)

# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY = settings.server_api_key

# Create API key header security scheme
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

class APIAuthService:
    """Service for handling API key authentication"""
    
    @staticmethod
    async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
        """
        Verify the API key from the request header
        
        Args:
            api_key: The API key from the X-API-Key header
            
        Returns:
            str: The verified API key
            
        Raises:
            HTTPException: If the API key is invalid or missing
        """
        try:
            # Check if API key is provided
            if not api_key:
                logger.warning("API key missing from request headers")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key is required. Please provide X-API-Key header.",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            
            # Check if API key matches the configured key
            if api_key != API_KEY:
                logger.warning(f"Invalid API key provided: {api_key[:8]}...")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key provided.",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            
            # Log successful authentication (without exposing the key)
            logger.info("API key authentication successful")
            return api_key
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during API key verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )
    
    @staticmethod
    def is_api_key_configured() -> bool:
        """
        Check if API key is properly configured
        
        Returns:
            bool: True if API key is configured, False otherwise
        """
        return bool(API_KEY and API_KEY.strip())
    
    @staticmethod
    def get_api_key_info() -> dict:
        """
        Get API key configuration information (for debugging/monitoring)
        
        Returns:
            dict: API key configuration info
        """
        return {
            "api_key_configured": APIAuthService.is_api_key_configured(),
            "api_key_header_name": API_KEY_NAME,
            "api_key_length": len(API_KEY) if API_KEY else 0,
            "api_key_prefix": API_KEY[:8] + "..." if API_KEY and len(API_KEY) > 8 else "Not configured"
        }

# Convenience function for dependency injection
async def get_verified_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency for API key verification
    
    Usage:
        @router.post("/endpoint")
        async def my_endpoint(api_key: str = Depends(get_verified_api_key)):
            # This endpoint is now protected by API key authentication
            pass
    """
    return await APIAuthService.verify_api_key(api_key)
