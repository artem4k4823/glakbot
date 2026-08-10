from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User
from app.schemas.user_schemas import UserCreate


class UserRepository:
    """Async repository for User management via SQLAlchemy 2.0."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_users(self) -> List[User]:
        stmt = select(User).order_by(User.id.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        stmt = select(User).where(User.discord_id == discord_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user_in: UserCreate) -> User:
        user = User(
            discord_id=user_in.discord_id,
            username=user_in.username,
            email=user_in.email,
            is_admin=user_in.is_admin
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
