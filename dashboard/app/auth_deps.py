import httpx
import jwt
from typing import Optional, List, Dict
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database.session import get_async_db as get_db
from app.database.models.user import User

GUILDS_URL = "https://discord.com/api/users/@me/guilds"


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """Получает текущего пользователя из JWT токена в куках."""
    token = request.cookies.get("session")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        discord_id: str = payload.get("sub")
        if discord_id is None:
            return None
    except jwt.PyJWTError:
        return None
        
    stmt = select(User).where(User.discord_id == discord_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Auto-promote to superadmin if in settings
    if user and str(user.discord_id) in settings.SUPERADMIN_IDS:
        if not user.is_admin:
            user.is_admin = True
            await db.commit()
    
    # Мы можем временно сохранить access_token в объекте, если нам нужно делать запросы к Discord API
    if user:
        user.discord_access_token = payload.get("access_token")
        
    return user


async def get_superadmin_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """Требует прав супер-администратора."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized as superadmin")
    return user


async def get_user_guilds(user: User) -> List[Dict]:
    """Получает список серверов пользователя из Discord API."""
    if not hasattr(user, "discord_access_token") or not user.discord_access_token:
        return []
        
    headers = {"Authorization": f"Bearer {user.discord_access_token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(GUILDS_URL, headers=headers)
        if resp.status_code == 200:
            return resp.json()
    return []


import time

bot_guilds_cache = {"guilds": set(), "timestamp": 0}

async def get_bot_guilds() -> set:
    """Получает множество ID серверов, на которых есть бот (кешируется на 5 сек)."""
    if time.time() - bot_guilds_cache["timestamp"] < 5:
        return bot_guilds_cache["guilds"]
        
    if not settings.BOT_TOKEN:
        return set()
        
    headers = {"Authorization": f"Bot {settings.BOT_TOKEN}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(GUILDS_URL, headers=headers)
            if resp.status_code == 200:
                guilds = resp.json()
                guild_ids = {g["id"] for g in guilds}
                bot_guilds_cache["guilds"] = guild_ids
                bot_guilds_cache["timestamp"] = time.time()
                return guild_ids
        except Exception:
            pass
    return set()


async def get_admin_guilds(guilds: List[Dict]) -> List[Dict]:
    """Фильтрует список серверов и проверяет наличие бота."""
    admin_guilds = []
    bot_guilds = await get_bot_guilds()
    
    for g in guilds:
        perms = int(g.get("permissions", 0))
        if perms & 0x8:
            g["bot_joined"] = g["id"] in bot_guilds
            admin_guilds.append(g)
    return admin_guilds
