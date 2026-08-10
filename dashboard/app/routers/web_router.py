from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.session import get_async_db
from app.services.ticket_service import TicketService
from app.services.user_service import UserService
from app.auth_deps import get_current_user, get_user_guilds, get_admin_guilds
from app.database.models.user import User
from app.config import settings

router = APIRouter(tags=["Web Pages"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if not user:
        # Покажем страницу авторизации
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "page_title": "Добро пожаловать",
                "active_page": "dashboard",
                "user": None
            }
        )
    
    # Запрашиваем гильдии пользователя
    guilds = await get_user_guilds(user)
    admin_guilds = await get_admin_guilds(guilds)
    
    return templates.TemplateResponse(
        request=request,
        name="server_list.html",
        context={
            "page_title": "Ваши серверы",
            "active_page": "dashboard",
            "user": user,
            "guilds": admin_guilds,
            "client_id": settings.DISCORD_CLIENT_ID
        }
    )


from app.services.ticket_service import TicketService, get_ticket_service


@router.get("/server/{guild_id}", response_class=HTMLResponse)
async def server_dashboard(
    guild_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if not user:
        return RedirectResponse("/auth/login")
        
    service = get_ticket_service(guild_id, db)
    stats = await service.get_stats()
    recent_tickets = await service.list_tickets()
    categories = await service.list_categories()
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": "Дашборд сервера",
            "active_page": "dashboard",
            "user": user,
            "guild_id": guild_id,
            "stats": stats,
            "tickets": recent_tickets[:5],
            "categories": categories
        }
    )


@router.get("/server/{guild_id}/categories", response_class=HTMLResponse)
async def categories_page(
    guild_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if not user:
        return RedirectResponse("/auth/login")
        
    service = get_ticket_service(guild_id, db)
    categories = await service.list_categories()
    
    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={
            "page_title": "Категории тикетов",
            "active_page": "categories",
            "user": user,
            "guild_id": guild_id,
            "categories": categories
        }
    )


@router.get("/server/{guild_id}/tickets", response_class=HTMLResponse)
async def tickets_page(
    guild_id: str,
    request: Request,
    status: str = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if not user:
        return RedirectResponse("/auth/login")
        
    service = get_ticket_service(guild_id, db)
    tickets = await service.list_tickets(status=status)
    
    return templates.TemplateResponse(
        request=request,
        name="tickets.html",
        context={
            "page_title": "Все тикеты",
            "active_page": "tickets",
            "user": user,
            "guild_id": guild_id,
            "tickets": tickets,
            "current_status": status or "all"
        }
    )


@router.get("/server/{guild_id}/settings", response_class=HTMLResponse)
async def settings_page(
    guild_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if not user:
        return RedirectResponse("/auth/login")
        
    service = get_ticket_service(guild_id, db)
    config = await service.get_panel_config()
    
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "page_title": "Настройки панели",
            "active_page": "settings",
            "user": user,
            "guild_id": guild_id,
            "config": config
        }
    )


from app.auth_deps import get_superadmin_user

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    user: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_async_db)
):
    from sqlalchemy import select
    from app.database.models.user import User
    from app.database.models.guild_settings import GuildSettings
    
    # Get all users
    users_stmt = select(User).order_by(User.id)
    users_result = await db.execute(users_stmt)
    all_users = users_result.scalars().all()
    
    # Get all servers
    guilds_stmt = select(GuildSettings).order_by(GuildSettings.id)
    guilds_result = await db.execute(guilds_stmt)
    all_guilds = guilds_result.scalars().all()
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "page_title": "Панель администратора",
            "active_page": "admin",
            "user": user,
            "all_users": all_users,
            "all_guilds": all_guilds
        }
    )
