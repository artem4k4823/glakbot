import httpx
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database.session import get_async_db as get_db
from app.database.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USER_URL = "https://discord.com/api/users/@me"


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@router.get("/login")
async def login():
    """Перенаправление на страницу авторизации Discord."""
    redirect_uri = settings.DISCORD_REDIRECT_URI
    url = (
        f"{OAUTH_URL}?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&response_type=code&scope=identify%20guilds"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    """Обработка возврата от Discord и получение токена."""
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        # Получаем access token
        token_resp = await client.post(TOKEN_URL, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token from Discord")
        
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        
        # Получаем инфу о пользователе
        headers = {"Authorization": f"Bearer {access_token}"}
        user_resp = await client.get(USER_URL, headers=headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Discord")
        
        user_info = user_resp.json()
        discord_id = user_info.get("id")
        username = user_info.get("username")
        
        # Сохраняем или обновляем пользователя в БД
        stmt = select(User).where(User.discord_id == discord_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(discord_id=discord_id, username=username)
            db.add(user)
        else:
            user.username = username
            
        await db.commit()
        await db.refresh(user)
        
        # Создаем JWT
        jwt_token = create_access_token(
            data={"sub": str(user.discord_id), "access_token": access_token}
        )
        
        # Устанавливаем куку
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="session", 
            value=jwt_token, 
            httponly=True, 
            max_age=7 * 24 * 3600,
            samesite="lax",
            secure=settings.DISCORD_REDIRECT_URI.startswith("https://"),
        )
        return response


@router.get("/logout")
async def logout():
    """Выход из системы."""
    response = RedirectResponse(url="/")
    response.delete_cookie(key="session")
    return response
