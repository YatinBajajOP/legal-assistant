from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_db
from app.repositories.user_repository import get_or_create_mock_user
from fastapi import Depends


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Static/mock current-user dependency; swap for real auth later without touching callers."""
    return await get_or_create_mock_user(db)
