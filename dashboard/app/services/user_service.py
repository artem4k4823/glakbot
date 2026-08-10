from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user_schemas import UserCreate, UserResponse


class UserService:
    """Сервис управления пользователями."""

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def list_users(self) -> List[UserResponse]:
        users = await self.repository.get_all_users()
        return [UserResponse.model_validate(u) for u in users]

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        user = await self.repository.get_user_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def register_user(self, user_in: UserCreate) -> UserResponse:
        existing = await self.repository.get_user_by_discord_id(user_in.discord_id)
        if existing:
            return UserResponse.model_validate(existing)
        user = await self.repository.create_user(user_in)
        return UserResponse.model_validate(user)
