from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, declarative_base
from sqlalchemy import select, String, Text
from app.dashboard_service.core.base import Base


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