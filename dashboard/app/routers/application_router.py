from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_deps import get_current_user, require_guild_admin
from app.database.models.user import User
from app.database.session import get_async_db
from app.schemas.application_schemas import (
    ApplicationConfigSchema,
    ApplicationDecisionResult,
    ApplicationRejectRequest,
    ApplicationSchema,
)
from app.services import discord_api
from app.services.application_service import ApplicationError, ApplicationService

router = APIRouter(tags=["Applications"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATUS_FILTERS = {"pending", "approved", "rejected"}


async def _page_user(guild_id: str, user: Optional[User]) -> User | RedirectResponse:
    if not user:
        return RedirectResponse("/auth/login")
    return await require_guild_admin(guild_id, user)


# --- WEB PAGES ---

@router.get("/server/{guild_id}/applications", response_class=HTMLResponse)
async def applications_page(
    guild_id: str,
    request: Request,
    status: str = "pending",
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    user = await _page_user(guild_id, user)
    if isinstance(user, RedirectResponse):
        return user

    service = ApplicationService(db, guild_id)
    status_filter = status if status in STATUS_FILTERS else None
    config = await service.get_config()

    return templates.TemplateResponse(
        request=request,
        name="applications.html",
        context={
            "page_title": "Анкеты",
            "active_page": "applications",
            "user": user,
            "guild_id": guild_id,
            "applications": await service.list_applications(status=status_filter),
            "counts": await service.count_by_status(),
            "current_status": status_filter or "all",
            "role_configured": bool(config.approved_role_id),
        },
    )


@router.get("/server/{guild_id}/application-settings", response_class=HTMLResponse)
async def application_settings_page(
    guild_id: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    user = await _page_user(guild_id, user)
    if isinstance(user, RedirectResponse):
        return user

    config = await ApplicationService(db, guild_id).get_config()
    return templates.TemplateResponse(
        request=request,
        name="application_settings.html",
        context={
            "page_title": "Настройки анкеты",
            "active_page": "application_settings",
            "user": user,
            "guild_id": guild_id,
            "config": config,
            "questions_json": [q.model_dump() for q in config.questions],
            "roles": await discord_api.get_guild_roles(guild_id),
            "channels": await discord_api.get_guild_text_channels(guild_id),
        },
    )


# --- API ---

def _raise(e: ApplicationError):
    raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/api/v1/applications", response_model=List[ApplicationSchema])
async def api_list_applications(
    guild_id: str,
    status: Optional[str] = None,
    user: User = Depends(require_guild_admin),
    db: AsyncSession = Depends(get_async_db),
):
    return await ApplicationService(db, guild_id).list_applications(status=status)


@router.post("/api/v1/applications/{application_id}/approve", response_model=ApplicationDecisionResult)
async def api_approve_application(
    application_id: str,
    guild_id: str,
    user: User = Depends(require_guild_admin),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await ApplicationService(db, guild_id).approve(application_id, user)
    except ApplicationError as e:
        _raise(e)


@router.post("/api/v1/applications/{application_id}/reject", response_model=ApplicationDecisionResult)
async def api_reject_application(
    application_id: str,
    guild_id: str,
    body: ApplicationRejectRequest,
    user: User = Depends(require_guild_admin),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await ApplicationService(db, guild_id).reject(application_id, user, body.reason)
    except ApplicationError as e:
        _raise(e)


@router.get("/api/v1/application-config", response_model=ApplicationConfigSchema)
async def api_get_application_config(
    guild_id: str,
    user: User = Depends(require_guild_admin),
    db: AsyncSession = Depends(get_async_db),
):
    return await ApplicationService(db, guild_id).get_config()


@router.post("/api/v1/application-config", response_model=ApplicationConfigSchema)
async def api_save_application_config(
    guild_id: str,
    config_in: ApplicationConfigSchema,
    user: User = Depends(require_guild_admin),
    db: AsyncSession = Depends(get_async_db),
):
    return await ApplicationService(db, guild_id).save_config(config_in)
