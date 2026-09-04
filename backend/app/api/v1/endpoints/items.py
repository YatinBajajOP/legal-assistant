from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.item import ItemCreate, ItemPublic
from app.services import crud

router = APIRouter()

@router.post("/", response_model=ItemPublic)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new item."""
    item = await crud.create_item(db=db, item=item_in)
    return item

@router.get("/{item_id}", response_model=ItemPublic)
async def read_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get item by ID."""
    item = await crud.get_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
