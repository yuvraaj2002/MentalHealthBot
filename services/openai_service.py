from typing import Optional, Dict, Any
from models.base import BaseResponse

class ExampleService:
    """Example service class to demonstrate service layer usage"""
    
    def __init__(self):
        self.data_store: Dict[str, Any] = {}
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item by ID"""
        return self.data_store.get(item_id)
    
    async def create_item(self, item_id: str, data: Dict[str, Any]) -> BaseResponse:
        """Create a new item"""
        if item_id in self.data_store:
            return BaseResponse(
                success=False,
                message=f"Item with ID {item_id} already exists"
            )
        
        self.data_store[item_id] = data
        return BaseResponse(message=f"Item {item_id} created successfully")
    
    async def update_item(self, item_id: str, data: Dict[str, Any]) -> BaseResponse:
        """Update an existing item"""
        if item_id not in self.data_store:
            return BaseResponse(
                success=False,
                message=f"Item with ID {item_id} not found"
            )
        
        self.data_store[item_id].update(data)
        return BaseResponse(message=f"Item {item_id} updated successfully")
    
    async def delete_item(self, item_id: str) -> BaseResponse:
        """Delete an item by ID"""
        if item_id not in self.data_store:
            return BaseResponse(
                success=False,
                message=f"Item with ID {item_id} not found"
            )
        
        del self.data_store[item_id]
        return BaseResponse(message=f"Item {item_id} deleted successfully")
