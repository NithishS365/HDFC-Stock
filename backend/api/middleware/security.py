"""
Security Middleware
API key verification and rate limiting
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import os

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key for protected endpoints
    
    Note: For production, implement proper authentication
    """
    # For now, allow requests without API key (open API)
    # In production, uncomment and set API_KEY in environment
    
    # expected_api_key = os.getenv("API_KEY")
    # if not expected_api_key:
    #     # If no API key is set, allow all requests (dev mode)
    #     return True
    
    # if not api_key or api_key != expected_api_key:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid or missing API key"
    #     )
    
    return True
