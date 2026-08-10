import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import settings
from app.schemas.ticket_schemas import (
    CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    TicketSchema,
    TicketCreate,
    PanelConfigSchema
)


class TicketRepository:
    """Репозиторий для управления категориями, тикетами и конфигурацией панели."""

    def __init__(self, storage_file: Path = settings.DATA_FILE):
        self.storage_file = storage_file
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        if not self.storage_file.parent.exists():
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.storage_file.exists():
            default_data = {
                "categories": [
                    {
                        "id": "tech-support",
                        "label": "Техническая поддержка",
                        "description": "Вопросы по работе бота, ошибки и сбои",
                        "emoji": "🛠️"
                    },
                    {
                        "id": "billing",
                        "label": "Вопросы по оплате / подписке",
                        "description": "Помощь с платежами и привилегиями",
                        "emoji": "💳"
                    },
                    {
                        "id": "feedback",
                        "label": "Жалобы и предложения",
                        "description": "Сообщить о нарушении или предложить идею",
                        "emoji": "📜"
                    },
                    {
                        "id": "general",
                        "label": "Общие вопросы",
                        "description": "Любые другие темы и консультации",
                        "emoji": "❓"
                    }
                ],
                "tickets": [],
                "panel_config": {
                    "title": "🎫 Поддержка и обратная связь",
                    "description": "Добро пожаловать в центр поддержки!",
                    "color": "#5865F2",
                    "banner_url": "https://images.unsplash.com/photo-1534536281715-e28d76689b4d?w=1200&q=80",
                    "footer_text": "Служба поддержки • Нажмите на кнопку ниже, чтобы начать"
                }
            }
            self._save_raw_data(default_data)

    def _load_raw_data(self) -> Dict[str, Any]:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"categories": [], "tickets": [], "panel_config": {}}

    def _save_raw_data(self, data: Dict[str, Any]):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- CATEGORIES ---

    def get_all_categories(self) -> List[CategorySchema]:
        data = self._load_raw_data()
        return [CategorySchema(**cat) for cat in data.get("categories", [])]

    def get_category_by_id(self, category_id: str) -> Optional[CategorySchema]:
        categories = self.get_all_categories()
        for cat in categories:
            if cat.id == category_id:
                return cat
        return None

    def add_category(self, category_data: CategoryCreate) -> CategorySchema:
        data = self._load_raw_data()
        cat_id = f"cat-{uuid.uuid4().hex[:8]}"
        new_category = CategorySchema(
            id=cat_id,
            label=category_data.label,
            description=category_data.description,
            emoji=category_data.emoji
        )
        data.setdefault("categories", []).append(new_category.model_dump())
        self._save_raw_data(data)
        return new_category

    def update_category(self, category_id: str, update_data: CategoryUpdate) -> Optional[CategorySchema]:
        data = self._load_raw_data()
        categories = data.get("categories", [])
        for i, cat in enumerate(categories):
            if cat["id"] == category_id:
                if update_data.label is not None:
                    cat["label"] = update_data.label
                if update_data.description is not None:
                    cat["description"] = update_data.description
                if update_data.emoji is not None:
                    cat["emoji"] = update_data.emoji
                categories[i] = cat
                self._save_raw_data(data)
                return CategorySchema(**cat)
        return None

    def delete_category(self, category_id: str) -> bool:
        data = self._load_raw_data()
        categories = data.get("categories", [])
        initial_len = len(categories)
        data["categories"] = [cat for cat in categories if cat["id"] != category_id]
        if len(data["categories"]) < initial_len:
            self._save_raw_data(data)
            return True
        return False

    # --- TICKETS ---

    def get_all_tickets(self) -> List[TicketSchema]:
        data = self._load_raw_data()
        return [TicketSchema(**t) for t in data.get("tickets", [])]

    def add_ticket(self, ticket_data: TicketCreate) -> TicketSchema:
        data = self._load_raw_data()
        ticket_id = f"t-{len(data.get('tickets', [])) + 1001}"
        from datetime import datetime
        now_str = datetime.now().isoformat()
        
        new_ticket = TicketSchema(
            id=ticket_id,
            user_name=ticket_data.user_name,
            user_id=ticket_data.user_id,
            category=ticket_data.category,
            subject=ticket_data.subject,
            description=ticket_data.description,
            channel_id=ticket_data.channel_id,
            status="open",
            created_at=now_str
        )
        data.setdefault("tickets", []).insert(0, new_ticket.model_dump())
        self._save_raw_data(data)
        return new_ticket

    def update_ticket_status(self, ticket_id: str, status: str) -> Optional[TicketSchema]:
        data = self._load_raw_data()
        tickets = data.get("tickets", [])
        for i, t in enumerate(tickets):
            if t["id"] == ticket_id:
                t["status"] = status
                tickets[i] = t
                self._save_raw_data(data)
                return TicketSchema(**t)
        return None

    # --- PANEL CONFIG ---

    def get_panel_config(self) -> PanelConfigSchema:
        data = self._load_raw_data()
        return PanelConfigSchema(**data.get("panel_config", {}))

    def update_panel_config(self, config: PanelConfigSchema) -> PanelConfigSchema:
        data = self._load_raw_data()
        data["panel_config"] = config.model_dump()
        self._save_raw_data(data)
        return config


_repository_instance: Optional[TicketRepository] = None

def get_ticket_repository() -> TicketRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = TicketRepository()
    return _repository_instance
