from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class CategoryModel(Base):
    """Модель категории тикета в PostgreSQL."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    emoji: Mapped[str] = mapped_column(String(20), default="🎫", nullable=False)


class TicketModel(Base):
    """Модель тикета в PostgreSQL."""

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class PanelConfigModel(Base):
    """Модель конфигурации панели Embed тикета."""

    __tablename__ = "panel_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="🎫 Поддержка и обратная связь")
    description: Mapped[str] = mapped_column(Text, default="Добро пожаловать в центр поддержки!")
    color: Mapped[str] = mapped_column(String(20), default="#5865F2")
    banner_url: Mapped[str] = mapped_column(String(500), default="https://images.unsplash.com/photo-1534536281715-e28d76689b4d?w=1200&q=80")
    footer_text: Mapped[str] = mapped_column(String(255), default="Служба поддержки • Нажмите на кнопку ниже, чтобы начать")
