import os
import discord
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, declarative_base
from sqlalchemy import select, String, Text

from dotenv import load_dotenv
from pathlib import Path

# Попробуем загрузить .env
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgrespassword@localhost:5437/snaphelp_db"
)

# Создаем движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class CategoryModel(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    emoji: Mapped[str] = mapped_column(String(10))

class TicketModel(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    channel_id: Mapped[str] = mapped_column(String(64))
    user_name: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))

class PanelConfigModel(Base):
    __tablename__ = "panel_configs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(100), default="🎫 Поддержка и обратная связь")
    description: Mapped[str] = mapped_column(Text, default="Добро пожаловать в центр поддержки!")
    color: Mapped[str] = mapped_column(String(20), default="#5865F2")
    banner_url: Mapped[Optional[str]] = mapped_column(String(255))
    footer_text: Mapped[str] = mapped_column(String(100), default="Служба поддержки")


class TicketDashboardManager:
    """
    Менеджер интеграции Discord-бота с базой данных PostgreSQL (Multi-Tenancy).
    """

    async def get_ticket_options(self, guild_id: str) -> List[discord.SelectOption]:
        """Возвращает актуальный список категорий для сервера."""
        async with async_session() as db:
            stmt = select(CategoryModel).where(CategoryModel.guild_id == str(guild_id))
            result = await db.execute(stmt)
            categories = result.scalars().all()
            
            if not categories:
                return [
                    discord.SelectOption(
                        label="Общие вопросы",
                        description="Любые другие темы и консультации",
                        emoji="❓"
                    )
                ]

            options = []
            for cat in categories:
                options.append(
                    discord.SelectOption(
                        label=cat.label,
                        description=cat.description,
                        emoji=cat.emoji,
                        value=cat.label
                    )
                )
            return options

    async def get_panel_embed_data(self, guild_id: str) -> Dict[str, Any]:
        """Возвращает кастомные настройки панели для сервера."""
        async with async_session() as db:
            stmt = select(PanelConfigModel).where(PanelConfigModel.guild_id == str(guild_id))
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                return {
                    "title": config.title,
                    "description": config.description,
                    "color": config.color,
                    "banner_url": config.banner_url,
                    "footer_text": config.footer_text
                }
            
            return {
                "title": "🎫 Поддержка и обратная связь",
                "description": "Добро пожаловать в центр поддержки!",
                "color": "#5865F2",
                "footer_text": "Служба поддержки • Нажмите на кнопку ниже, чтобы начать"
            }

    async def register_ticket(
        self,
        guild_id: str,
        user_name: str,
        user_id: str,
        category: str,
        subject: str,
        description: str,
        channel_id: str | None = None
    ) -> str:
        """Регистрирует новый тикет в PostgreSQL."""
        import uuid
        ticket_id = f"t-{uuid.uuid4().hex[:8]}"
        
        async with async_session() as db:
            new_ticket = TicketModel(
                id=ticket_id,
                guild_id=str(guild_id),
                channel_id=str(channel_id) if channel_id else "",
                user_name=user_name,
                user_id=str(user_id),
                category=category,
                subject=subject,
                description=description,
                status="open"
            )
            db.add(new_ticket)
            await db.commit()
            
        return ticket_id

    async def update_ticket_status(self, guild_id: str, channel_id: str, status: str = "closed"):
        """Обновляет статус тикета по ID канала."""
        async with async_session() as db:
            stmt = select(TicketModel).where(
                TicketModel.guild_id == str(guild_id),
                TicketModel.channel_id == str(channel_id)
            )
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.status = status
                await db.commit()
