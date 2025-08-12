from fastapi import APIRouter, HTTPException
from models.base import BaseResponse, ErrorResponse

router = APIRouter(prefix="/api/v1", tags=["API"])

@router.get("/example", response_model=BaseResponse)
async def example_endpoint():
    """Example endpoint to demonstrate router usage"""
    return BaseResponse(message="This is an example endpoint from the API router")

@router.get("/example/{item_id}", response_model=BaseResponse)
async def example_with_param(item_id: int):
    """Example endpoint with path parameter"""
    if item_id < 0:
        raise HTTPException(status_code=400, detail="Item ID must be positive")
    return BaseResponse(message=f"Example endpoint with item ID: {item_id}")
