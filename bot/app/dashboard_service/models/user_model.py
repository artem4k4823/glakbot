from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, declarative_base
from sqlalchemy import select, String, Text
from app.dashboard_service.core.base import Base





class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discord_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)