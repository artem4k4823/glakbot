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
from app.schemas.user_schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api/v1", tags=["API Endpoints"])


# --- STATS ---

@router.get("/stats", response_model=DashboardStats)
async def get_stats(service: TicketService = Depends(get_ticket_service)):
    return await service.get_stats()


# --- USERS & SETTINGS ---

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_async_db)):
    user_service = UserService(db)
    return await user_service.list_users()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_db)):
    user_service = UserService(db)
    return await user_service.register_user(user_in)





# --- CATEGORIES ---

@router.get("/categories", response_model=List[CategorySchema])
async def list_categories(service: TicketService = Depends(get_ticket_service)):
    return await service.list_categories()


@router.post("/categories", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    service: TicketService = Depends(get_ticket_service)
):
    return await service.create_category(category_in)


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
    return await service.list_tickets(status=status)


@router.post("/tickets", response_model=TicketSchema, status_code=status.HTTP_201_CREATED)
async def register_ticket(
    ticket_in: TicketCreate,
    service: TicketService = Depends(get_ticket_service)
):
    return await service.register_ticket(ticket_in)


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
    return await service.get_panel_config()


@router.post("/config", response_model=PanelConfigSchema)
async def update_panel_config(
    config_in: PanelConfigSchema,
    service: TicketService = Depends(get_ticket_service)
):
    return await service.save_panel_config(config_in)


# --- ADMIN ---
from app.auth_deps import get_superadmin_user
from sqlalchemy import select

@router.post("/admin/users/{user_id}/toggle")
async def toggle_user_ban(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user=Depends(get_superadmin_user)
):
    from app.database.models.user import User
    
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    target_user.is_active = not target_user.is_active
    await db.commit()
    return {"status": "success", "is_active": target_user.is_active}


@router.post("/admin/servers/{guild_id}/toggle")
async def toggle_server_ban(
    guild_id: str,
    db: AsyncSession = Depends(get_async_db),
    admin_user=Depends(get_superadmin_user)
):
    from app.database.models.guild_settings import GuildSettings
    
    stmt = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
    res = await db.execute(stmt)
    server = res.scalar_one_or_none()
    
    if not server:
        # If server settings don't exist yet, create them disabled
        server = GuildSettings(guild_id=guild_id, is_active=False)
        db.add(server)
    else:
        server.is_active = not server.is_active
        
    await db.commit()
    return {"status": "success", "is_active": server.is_active}
