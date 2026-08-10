from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.postgres_ticket_repository import PostgresTicketRepository
from app.schemas.ticket_schemas import (
    CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    TicketSchema,
    TicketCreate,
    PanelConfigSchema,
    DashboardStats
)


class TicketService:
    """Асинхронный сервисный слой бизнес-логики тикет-системы."""

    def __init__(self, db: AsyncSession, guild_id: str):
        self.repository = PostgresTicketRepository(db, guild_id)

    # --- STATS ---

    async def get_stats(self) -> DashboardStats:
        tickets = await self.repository.get_all_tickets()
        categories = await self.repository.get_all_categories()
        
        open_count = sum(1 for t in tickets if t.status == "open")
        closed_count = sum(1 for t in tickets if t.status in ("closed", "resolved"))

        return DashboardStats(
            total_tickets=len(tickets),
            open_tickets=open_count,
            closed_tickets=closed_count,
            total_categories=len(categories)
        )

    # --- CATEGORIES ---

    async def list_categories(self) -> List[CategorySchema]:
        return await self.repository.get_all_categories()

    async def create_category(self, category_in: CategoryCreate) -> CategorySchema:
        return await self.repository.add_category(category_in)

    async def update_category(self, category_id: str, update_in: CategoryUpdate) -> Optional[CategorySchema]:
        return await self.repository.update_category(category_id, update_in)

    async def delete_category(self, category_id: str) -> bool:
        return await self.repository.delete_category(category_id)

    # --- TICKETS ---

    async def list_tickets(self, status: Optional[str] = None) -> List[TicketSchema]:
        tickets = await self.repository.get_all_tickets()
        if status:
            return [t for t in tickets if t.status == status]
        return tickets

    async def register_ticket(self, ticket_in: TicketCreate) -> TicketSchema:
        return await self.repository.add_ticket(ticket_in)

    async def update_ticket_status(self, ticket_id: str, status: str) -> Optional[TicketSchema]:
        return await self.repository.update_ticket_status(ticket_id, status)

    # --- PANEL CONFIG ---

    async def get_panel_config(self) -> PanelConfigSchema:
        return await self.repository.get_panel_config()

    async def save_panel_config(self, config_in: PanelConfigSchema) -> PanelConfigSchema:
        return await self.repository.update_panel_config(config_in)
