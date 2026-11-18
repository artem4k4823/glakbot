from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.application import ApplicationConfigModel, ApplicationModel
from app.database.models.user import User
from app.schemas.application_schemas import (
    ApplicationConfigSchema,
    ApplicationDecisionResult,
    ApplicationSchema,
)
from app.services import discord_api

COLOR_APPROVED = 0x10B981
COLOR_REJECTED = 0xEF4444


class ApplicationError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _render(template: str, **values: str) -> str:
    # Простая подстановка без str.format, чтобы фигурные скобки в тексте админа ничего не ломали
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


class ApplicationService:
    def __init__(self, db: AsyncSession, guild_id: str):
        self.db = db
        self.guild_id = guild_id

    # --- CONFIG ---

    async def _get_config_row(self) -> Optional[ApplicationConfigModel]:
        stmt = select(ApplicationConfigModel).where(ApplicationConfigModel.guild_id == self.guild_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_config(self) -> ApplicationConfigSchema:
        row = await self._get_config_row()
        return ApplicationConfigSchema.model_validate(row) if row else ApplicationConfigSchema()

    async def save_config(self, config_in: ApplicationConfigSchema) -> ApplicationConfigSchema:
        row = await self._get_config_row()
        if not row:
            row = ApplicationConfigModel(guild_id=self.guild_id)
            self.db.add(row)

        data = config_in.model_dump()
        data["questions"] = [q.model_dump() for q in config_in.questions]
        for field, value in data.items():
            setattr(row, field, value)

        await self.db.commit()
        await self.db.refresh(row)
        return ApplicationConfigSchema.model_validate(row)

    # --- APPLICATIONS ---

    async def list_applications(self, status: Optional[str] = None) -> List[ApplicationSchema]:
        stmt = select(ApplicationModel).where(ApplicationModel.guild_id == self.guild_id)
        if status:
            stmt = stmt.where(ApplicationModel.status == status)
        stmt = stmt.order_by(ApplicationModel.created_at.desc())
        rows = (await self.db.execute(stmt)).scalars().all()
        return [ApplicationSchema.model_validate(r) for r in rows]

    async def count_by_status(self) -> Dict[str, int]:
        stmt = (
            select(ApplicationModel.status, func.count())
            .where(ApplicationModel.guild_id == self.guild_id)
            .group_by(ApplicationModel.status)
        )
        counts = {"pending": 0, "approved": 0, "rejected": 0}
        for status, count in (await self.db.execute(stmt)).all():
            counts[status] = count
        counts["all"] = sum(counts.values())
        return counts

    async def _get_pending_for_update(self, application_id: str) -> ApplicationModel:
        # FOR UPDATE — чтобы два админа одновременно не обработали одну анкету
        stmt = (
            select(ApplicationModel)
            .where(ApplicationModel.guild_id == self.guild_id, ApplicationModel.id == application_id)
            .with_for_update()
        )
        application = (await self.db.execute(stmt)).scalar_one_or_none()
        if not application:
            raise ApplicationError(404, "Анкета не найдена")
        if application.status != "pending":
            raise ApplicationError(409, "Эта анкета уже рассмотрена")
        return application

    async def _finish(
        self,
        application: ApplicationModel,
        config: ApplicationConfigSchema,
        reviewer: User,
        status: str,
        dm_text: str,
    ) -> ApplicationDecisionResult:
        approved = status == "approved"
        application.status = status
        application.reviewer_id = reviewer.discord_id
        application.reviewer_name = reviewer.username
        application.reviewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(application)

        color = COLOR_APPROVED if approved else COLOR_REJECTED

        dm_sent = None
        if config.dm_on_decision:
            dm_sent = await discord_api.send_dm(
                application.user_id,
                {"description": dm_text, "color": color},
            )

        if application.review_channel_id and application.review_message_id:
            verdict = "✅ Одобрено" if approved else "❌ Отклонено"
            await discord_api.mark_review_message(
                application.review_channel_id,
                application.review_message_id,
                f"{verdict} • {reviewer.username}",
                color,
            )

        return ApplicationDecisionResult(
            application=ApplicationSchema.model_validate(application),
            dm_sent=dm_sent,
        )

    async def approve(self, application_id: str, reviewer: User) -> ApplicationDecisionResult:
        config = await self.get_config()
        if not config.approved_role_id:
            raise ApplicationError(400, "Сначала выберите роль для одобренных анкет в «Настройках анкеты»")

        application = await self._get_pending_for_update(application_id)

        try:
            await discord_api.add_member_role(
                self.guild_id,
                application.user_id,
                config.approved_role_id,
                reason=f"Анкета {application.id} одобрена ({reviewer.username})",
            )
        except discord_api.DiscordAPIError as e:
            await self.db.rollback()
            raise ApplicationError(502, f"Не удалось выдать роль: {e}")

        server = await discord_api.get_guild_name(self.guild_id) if config.dm_on_decision else ""
        dm_text = _render(config.approve_message, server=server, user=f"<@{application.user_id}>")
        return await self._finish(application, config, reviewer, "approved", dm_text)

    async def reject(self, application_id: str, reviewer: User, reason: str) -> ApplicationDecisionResult:
        config = await self.get_config()
        application = await self._get_pending_for_update(application_id)
        application.reject_reason = reason.strip() or None

        server = await discord_api.get_guild_name(self.guild_id) if config.dm_on_decision else ""
        dm_text = _render(
            config.reject_message,
            server=server,
            user=f"<@{application.user_id}>",
            reason=application.reject_reason or "не указана",
        )
        return await self._finish(application, config, reviewer, "rejected", dm_text)
