from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.dashboard_service.core.base import Base


class ApplicationConfigModel(Base):
    """Настройки анкеты сервера (редактируются в веб-панели)."""

    __tablename__ = "application_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(20))
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    button_label: Mapped[str] = mapped_column(String(80))
    questions: Mapped[list] = mapped_column(JSON)
    approved_role_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ApplicationModel(Base):
    """Заполненная пользователем анкета."""

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    user_name: Mapped[str] = mapped_column(String(100))
    user_avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    answers: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    review_channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
