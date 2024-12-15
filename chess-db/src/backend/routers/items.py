# routers/items.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from database import get_db
from models import ItemCreate, ItemUpdate, ItemResponse
from repository import ItemRepository

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new item."""
    try:
        repo = ItemRepository(db)
        return await repo.create_item(item)
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create item")

@router.get("", response_model=List[ItemResponse])
async def read_items(
    db: AsyncSession = Depends(get_db)
):
    """Get all items."""
    try:
        repo = ItemRepository(db)
        return await repo.get_items()
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch items")

@router.get("/{item_id}", response_model=ItemResponse)
async def read_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific item by ID."""
    try:
        repo = ItemRepository(db)
        item = await repo.get_item(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch item")

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing item."""
    try:
        repo = ItemRepository(db)
        updated_item = await repo.update_item(item_id, item)
        if updated_item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update item")

@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an item."""
    try:
        repo = ItemRepository(db)
        success = await repo.delete_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete item")