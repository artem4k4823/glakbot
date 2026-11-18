from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApplicationConfigModel(Base):
    """Настройки анкеты для вступления на сервер."""

    __tablename__ = "application_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Внешний вид панели в Discord
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#5865F2", nullable=False)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    button_label: Mapped[str] = mapped_column(String(80), default="Заполнить анкету", nullable=False)

    # Список вопросов: [{label, placeholder, style, required, min_length, max_length}]
    questions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Что происходит при решении
    approved_role_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dm_on_decision: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approve_message: Mapped[str] = mapped_column(Text, nullable=False)
    reject_message: Mapped[str] = mapped_column(Text, nullable=False)


class ApplicationModel(Base):
    """Анкета, заполненная пользователем."""

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_avatar: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # [{question, answer}] — вопрос сохраняется вместе с ответом, чтобы правка анкеты не ломала старые записи
    answers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending|approved|rejected
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    review_channel_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_message_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
