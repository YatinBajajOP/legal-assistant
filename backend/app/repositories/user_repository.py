from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import User


async def get_or_create_mock_user(db: AsyncSession) -> User:
    """Return the single static/mock user, creating it on first use.

    Real authentication can later replace this with a lookup based on the
    authenticated principal without changing downstream code, since callers
    only depend on a `User` instance.
    """
    result = await db.execute(select(User).where(User.email == settings.MOCK_USER_EMAIL))
    user = result.scalars().first()
    if user is not None:
        return user

    user = User(email=settings.MOCK_USER_EMAIL, full_name=settings.MOCK_USER_FULL_NAME, is_active=1)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
