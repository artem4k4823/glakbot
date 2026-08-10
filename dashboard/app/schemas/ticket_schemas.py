from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryCreate(BaseModel):
    label: str = Field(..., min_length=2, max_length=50, description="Название категории")
    description: str = Field("", max_length=150, description="Описание категории")
    emoji: str = Field("🎫", max_length=10, description="Эмодзи категории")


class CategoryUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=150)
    emoji: Optional[str] = Field(None, max_length=10)


class CategorySchema(CategoryCreate):
    id: str = Field(..., description="Уникальный идентификатор категории")

    class Config:
        from_attributes = True


class TicketCreate(BaseModel):
    user_name: str
    user_id: str
    category: str
    subject: str
    description: str
    channel_id: Optional[str] = None


class TicketUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(open|closed|resolved)$")


class TicketSchema(TicketCreate):
    id: str
    status: str = "open"
    created_at: str

    class Config:
        from_attributes = True


class PanelConfigSchema(BaseModel):
    title: str = "🎫 Поддержка и обратная связь"
    description: str = "Добро пожаловать в центр поддержки!"
    color: str = "#5865F2"
    banner_url: str = "https://images.unsplash.com/photo-1534536281715-e28d76689b4d?w=1200&q=80"
    footer_text: str = "Служба поддержки • Нажмите на кнопку ниже, чтобы начать"

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    total_categories: int
