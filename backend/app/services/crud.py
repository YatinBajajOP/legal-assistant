from typing import Any, List, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item
from app.schemas.item import ItemCreate, ItemUpdate

ModelType = TypeVar("ModelType", bound=Any)

async def get_item(
    db: AsyncSession,
    item_id: int
) -> Optional[Item]:
    result = await db.execute(select(Item).filter(Item.id == item_id))
    return result.scalars().first()

async def create_item(
    db: AsyncSession,
    item: ItemCreate
) -> Item:
    db_item = Item(title=item.title, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item
