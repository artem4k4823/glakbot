from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.models.ticket import CategoryModel, TicketModel, PanelConfigModel
from app.schemas.ticket_schemas import (
    CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    TicketSchema,
    TicketCreate,
    PanelConfigSchema
)

class PostgresTicketRepository:
    """Асинхронный репозиторий для категорий, тикетов и настроек панели (PostgreSQL)."""

    def __init__(self, db: AsyncSession, guild_id: str):
        self.db = db
        self.guild_id = guild_id

    # --- CATEGORIES ---

    async def get_all_categories(self) -> List[CategorySchema]:
        stmt = select(CategoryModel).where(CategoryModel.guild_id == self.guild_id)
        result = await self.db.execute(stmt)
        categories = result.scalars().all()
        return [CategorySchema.model_validate(c) for c in categories]

    async def get_category_by_id(self, category_id: str) -> Optional[CategorySchema]:
        stmt = select(CategoryModel).where(CategoryModel.guild_id == self.guild_id, CategoryModel.id == category_id)
        result = await self.db.execute(stmt)
        cat = result.scalar_one_or_none()
        return CategorySchema.model_validate(cat) if cat else None

    async def add_category(self, category_data: CategoryCreate) -> CategorySchema:
        import uuid
        cat_id = f"cat-{uuid.uuid4().hex[:8]}"
        new_cat = CategoryModel(
            id=cat_id,
            guild_id=self.guild_id,
            label=category_data.label,
            description=category_data.description,
            emoji=category_data.emoji
        )
        self.db.add(new_cat)
        await self.db.commit()
        await self.db.refresh(new_cat)
        return CategorySchema.model_validate(new_cat)

    async def update_category(self, category_id: str, update_data: CategoryUpdate) -> Optional[CategorySchema]:
        stmt = select(CategoryModel).where(CategoryModel.guild_id == self.guild_id, CategoryModel.id == category_id)
        result = await self.db.execute(stmt)
        cat = result.scalar_one_or_none()
        if not cat:
            return None
            
        if update_data.label is not None:
            cat.label = update_data.label
        if update_data.description is not None:
            cat.description = update_data.description
        if update_data.emoji is not None:
            cat.emoji = update_data.emoji
            
        await self.db.commit()
        await self.db.refresh(cat)
        return CategorySchema.model_validate(cat)

    async def delete_category(self, category_id: str) -> bool:
        stmt = delete(CategoryModel).where(CategoryModel.guild_id == self.guild_id, CategoryModel.id == category_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    # --- TICKETS ---

    async def get_all_tickets(self) -> List[TicketSchema]:
        stmt = select(TicketModel).where(TicketModel.guild_id == self.guild_id).order_by(TicketModel.created_at.desc())
        result = await self.db.execute(stmt)
        tickets = result.scalars().all()
        return [TicketSchema.model_validate(t) for t in tickets]

    async def add_ticket(self, ticket_data: TicketCreate) -> TicketSchema:
        import uuid
        ticket_id = f"t-{uuid.uuid4().hex[:8]}"
        
        new_ticket = TicketModel(
            id=ticket_id,
            guild_id=self.guild_id,
            channel_id=ticket_data.channel_id,
            user_name=ticket_data.user_name,
            user_id=ticket_data.user_id,
            category=ticket_data.category,
            subject=ticket_data.subject,
            description=ticket_data.description,
            status="open"
        )
        self.db.add(new_ticket)
        await self.db.commit()
        await self.db.refresh(new_ticket)
        return TicketSchema.model_validate(new_ticket)

    async def update_ticket_status(self, ticket_id: str, status: str) -> Optional[TicketSchema]:
        stmt = select(TicketModel).where(TicketModel.guild_id == self.guild_id, TicketModel.id == ticket_id)
        result = await self.db.execute(stmt)
        ticket = result.scalar_one_or_none()
        if not ticket:
            return None
        ticket.status = status
        await self.db.commit()
        await self.db.refresh(ticket)
        return TicketSchema.model_validate(ticket)

    # --- PANEL CONFIG ---

    async def get_panel_config(self) -> PanelConfigSchema:
        stmt = select(PanelConfigModel).where(PanelConfigModel.guild_id == self.guild_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if not config:
            # Create default config
            config = PanelConfigModel(guild_id=self.guild_id)
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            
        return PanelConfigSchema.model_validate(config)

    async def update_panel_config(self, config_in: PanelConfigSchema) -> PanelConfigSchema:
        stmt = select(PanelConfigModel).where(PanelConfigModel.guild_id == self.guild_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if not config:
            config = PanelConfigModel(guild_id=self.guild_id)
            self.db.add(config)
            
        config.title = config_in.title
        config.description = config_in.description
        config.color = config_in.color
        config.banner_url = config_in.banner_url
        config.footer_text = config_in.footer_text
        
        await self.db.commit()
        await self.db.refresh(config)
        return PanelConfigSchema.model_validate(config)
