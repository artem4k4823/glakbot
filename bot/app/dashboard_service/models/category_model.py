from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, declarative_base
from sqlalchemy import select, String, Text
from app.dashboard_service.core.base import Base


class CategoryModel(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    emoji: Mapped[str] = mapped_column(String(10))