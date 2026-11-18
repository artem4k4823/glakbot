import uuid
from typing import List, Dict, Any, Optional

import discord
from sqlalchemy import select

from app.dashboard_service.core.database import async_session
from app.dashboard_service.models import (
    ApplicationConfigModel,
    ApplicationModel,
    CategoryModel,
    GuildSettingsModel,
    PanelConfigModel,
    TicketModel,
    UserModel,
)

DEFAULT_APPLICATION_QUESTIONS: List[Dict[str, Any]] = [
    {"label": "Как к вам обращаться?", "placeholder": "Имя или ник", "style": "short",
     "required": True, "min_length": 2, "max_length": 50},
    {"label": "Сколько вам лет?", "placeholder": "Например: 18", "style": "short",
     "required": True, "min_length": 1, "max_length": 3},
    {"label": "Откуда вы узнали о сервере?", "placeholder": "Друг, реклама, поиск...", "style": "short",
     "required": True, "min_length": 2, "max_length": 100},
    {"label": "Расскажите немного о себе", "placeholder": "Чем увлекаетесь, зачем пришли на сервер...",
     "style": "paragraph", "required": True, "min_length": 10, "max_length": 1000},
]

DEFAULT_APPLICATION_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "title": "📋 Анкета для вступления",
    "description": "Чтобы получить доступ к серверу, заполните короткую анкету. "
                   "Администрация рассмотрит её и выдаст роль.",
    "color": "#5865F2",
    "banner_url": None,
    "button_label": "Заполнить анкету",
    "questions": DEFAULT_APPLICATION_QUESTIONS,
    "approved_role_id": None,
    "review_channel_id": None,
}

class TicketDashboardManager:
    """
    Менеджер интеграции Discord-бота с базой данных PostgreSQL (Multi-Tenancy).
    """

    async def get_ticket_options(self, guild_id: str) -> List[discord.SelectOption]:
        """Возвращает актуальный список категорий для сервера."""
        async with async_session() as db:
            stmt = select(CategoryModel).where(CategoryModel.guild_id == str(guild_id))
            result = await db.execute(stmt)
            categories = result.scalars().all()
            
            if not categories:
                return [
                    discord.SelectOption(
                        label="Общие вопросы",
                        description="Любые другие темы и консультации",
                        emoji="❓"
                    )
                ]

            options = []
            for cat in categories:
                options.append(
                    discord.SelectOption(
                        label=cat.label,
                        description=cat.description,
                        emoji=cat.emoji,
                        value=cat.label
                    )
                )
            return options

    async def get_panel_embed_data(self, guild_id: str) -> Dict[str, Any]:
        """Возвращает кастомные настройки панели для сервера."""
        async with async_session() as db:
            stmt = select(PanelConfigModel).where(PanelConfigModel.guild_id == str(guild_id))
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                return {
                    "title": config.title,
                    "description": config.description,
                    "color": config.color,
                    "banner_url": config.banner_url,
                    "footer_text": config.footer_text,
                    "admin_role_ids": config.admin_role_ids.split(",") if config.admin_role_ids else []
                }
            
            return {
                "title": "🎫 Поддержка и обратная связь",
                "description": "Добро пожаловать в центр поддержки!",
                "color": "#5865F2",
                "footer_text": "Служба поддержки • Нажмите на кнопку ниже, чтобы начать"
            }

    async def register_ticket(
        self,
        guild_id: str,
        user_name: str,
        user_id: str,
        category: str,
        subject: str,
        description: str,
        channel_id: str | None = None
    ) -> str:
        """Регистрирует новый тикет в PostgreSQL."""
        ticket_id = f"t-{uuid.uuid4().hex[:8]}"
        
        async with async_session() as db:
            new_ticket = TicketModel(
                id=ticket_id,
                guild_id=str(guild_id),
                channel_id=str(channel_id) if channel_id else "",
                user_name=user_name,
                user_id=str(user_id),
                category=category,
                subject=subject,
                description=description,
                status="open"
            )
            db.add(new_ticket)
            await db.commit()
            
        return ticket_id

    async def update_ticket_status(self, guild_id: str, channel_id: str, status: str = "closed"):
        """Обновляет статус тикета по ID канала."""
        async with async_session() as db:
            stmt = select(TicketModel).where(
                TicketModel.guild_id == str(guild_id),
                TicketModel.channel_id == str(channel_id)
            )
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.status = status
                await db.commit()

    async def check_ban(self, user_id: str, guild_id: str) -> bool:
        """Проверяет, заблокирован ли пользователь или сервер. Возвращает True, если заблокирован."""
        async with async_session() as db:
            # Проверяем сервер
            stmt_guild = select(GuildSettingsModel.is_active).where(GuildSettingsModel.guild_id == str(guild_id))
            res_guild = await db.execute(stmt_guild)
            guild_active = res_guild.scalar_one_or_none()
            if guild_active is False:
                return True
                
            # Проверяем пользователя
            stmt_user = select(UserModel.is_active).where(UserModel.discord_id == str(user_id))
            res_user = await db.execute(stmt_user)
            user_active = res_user.scalar_one_or_none()
            if user_active is False:
                return True

        return False

    # --- APPLICATIONS (анкеты) ---

    async def get_application_config(self, guild_id: str) -> Dict[str, Any]:
        """Настройки анкеты сервера; если в панели ещё ничего не сохранено — значения по умолчанию."""
        async with async_session() as db:
            stmt = select(ApplicationConfigModel).where(ApplicationConfigModel.guild_id == str(guild_id))
            config = (await db.execute(stmt)).scalar_one_or_none()

        if not config:
            return dict(DEFAULT_APPLICATION_CONFIG)

        return {
            "enabled": config.enabled,
            "title": config.title,
            "description": config.description,
            "color": config.color,
            "banner_url": config.banner_url,
            "button_label": config.button_label,
            "questions": config.questions or DEFAULT_APPLICATION_QUESTIONS,
            "approved_role_id": config.approved_role_id,
            "review_channel_id": config.review_channel_id,
        }

    async def get_latest_application(self, guild_id: str, user_id: str) -> Optional[ApplicationModel]:
        """Последняя анкета пользователя на сервере (или None)."""
        async with async_session() as db:
            stmt = (
                select(ApplicationModel)
                .where(ApplicationModel.guild_id == str(guild_id), ApplicationModel.user_id == str(user_id))
                .order_by(ApplicationModel.created_at.desc())
                .limit(1)
            )
            return (await db.execute(stmt)).scalar_one_or_none()

    async def register_application(
        self,
        guild_id: str,
        user_id: str,
        user_name: str,
        user_avatar: str | None,
        answers: List[Dict[str, str]],
    ) -> str:
        """Сохраняет новую анкету со статусом pending."""
        application_id = f"a-{uuid.uuid4().hex[:8]}"
        async with async_session() as db:
            db.add(ApplicationModel(
                id=application_id,
                guild_id=str(guild_id),
                user_id=str(user_id),
                user_name=user_name,
                user_avatar=user_avatar,
                answers=answers,
                status="pending",
            ))
            await db.commit()
        return application_id

    async def set_application_review_message(self, application_id: str, channel_id: str, message_id: str):
        """Запоминает сообщение в канале модерации, чтобы веб-панель могла его обновить после решения."""
        async with async_session() as db:
            application = await db.get(ApplicationModel, application_id)
            if application:
                application.review_channel_id = str(channel_id)
                application.review_message_id = str(message_id)
                await db.commit()
