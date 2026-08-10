from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class GuildSettings(Base):
    """Модель настроек для конкретного сервера (SQLAlchemy 2.0 style)."""

    __tablename__ = "guild_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    
    log_channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    admin_role_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ticket_category_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
