from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from app.dashboard_service.core.base import Base


class PanelConfigModel(Base):
    __tablename__ = "panel_configs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(100), default="🎫 Поддержка и обратная связь")
    description: Mapped[str] = mapped_column(Text, default="Добро пожаловать в центр поддержки!")
    color: Mapped[str] = mapped_column(String(20), default="#5865F2")
    banner_url: Mapped[Optional[str]] = mapped_column(String(255))
    footer_text: Mapped[str] = mapped_column(String(100), default="Служба поддержки")
    admin_role_ids: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)