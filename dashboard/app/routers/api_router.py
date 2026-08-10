from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_async_db
from app.services.ticket_service import TicketService, get_ticket_service
from app.services.user_service import UserService
from app.schemas.ticket_schemas import (
    CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    TicketSchema,
    TicketCreate,
    TicketUpdateStatus,
    PanelConfigSchema,
    DashboardStats
)
from app.schemas.user_schemas import UserCreate, UserResponse, UserSettingsUpdate

router = APIRouter(prefix="/api/v1", tags=["API Endpoints"])


# --- STATS ---

@router.get("/stats", response_model=DashboardStats)
async def get_stats(service: TicketService = Depends(get_ticket_service)):
    return service.get_stats()


# --- USERS & SETTINGS ---

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_async_db)):
    user_service = UserService(db)
    return await user_service.list_users()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_db)):
    user_service = UserService(db)
    return await user_service.register_user(user_in)


@router.patch("/users/{user_id}/settings")
async def update_user_settings(
    user_id: int,
    settings_update: UserSettingsUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    user_service = UserService(db)
    updated = await user_service.update_settings(user_id, settings_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User settings not found")
    return {"status": "success", "message": "Settings updated"}


# --- CATEGORIES ---

@router.get("/categories", response_model=List[CategorySchema])
async def list_categories(service: TicketService = Depends(get_ticket_service)):
    return service.list_categories()


@router.post("/categories", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    service: TicketService = Depends(get_ticket_service)
):
    return service.create_category(category_in)


@router.patch("/categories/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: str,
    update_in: CategoryUpdate,
    service: TicketService = Depends(get_ticket_service)
):
    cat = service.update_category(category_id, update_in)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    service: TicketService = Depends(get_ticket_service)
):
    success = service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None


# --- TICKETS ---

@router.get("/tickets", response_model=List[TicketSchema])
async def list_tickets(
    status: str = None,
    service: TicketService = Depends(get_ticket_service)
):
    return service.list_tickets(status=status)


@router.post("/tickets", response_model=TicketSchema, status_code=status.HTTP_201_CREATED)
async def register_ticket(
    ticket_in: TicketCreate,
    service: TicketService = Depends(get_ticket_service)
):
    return service.register_ticket(ticket_in)


@router.patch("/tickets/{ticket_id}/status", response_model=TicketSchema)
async def update_ticket_status(
    ticket_id: str,
    status_in: TicketUpdateStatus,
    service: TicketService = Depends(get_ticket_service)
):
    ticket = service.update_ticket_status(ticket_id, status_in.status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# --- PANEL CONFIG ---

@router.get("/config", response_model=PanelConfigSchema)
async def get_panel_config(service: TicketService = Depends(get_ticket_service)):
    return service.get_panel_config()


@router.post("/config", response_model=PanelConfigSchema)
async def update_panel_config(
    config_in: PanelConfigSchema,
    service: TicketService = Depends(get_ticket_service)
):
    return service.save_panel_config(config_in)
