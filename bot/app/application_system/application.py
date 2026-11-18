import datetime

import discord
from discord.ui import InputText, Modal, View, button

from app.dashboard_service.manager import TicketDashboardManager

db_manager = TicketDashboardManager()

MAX_MODAL_FIELDS = 5  # ограничение Discord на количество полей в модальном окне


def _parse_color(hex_color: str | None) -> discord.Color:
    try:
        return discord.Color(int((hex_color or "#5865F2").lstrip("#"), 16))
    except ValueError:
        return discord.Color.blurple()


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _has_role(member: discord.abc.User, role_id: str | None) -> bool:
    if not role_id:
        return False
    return any(str(role.id) == str(role_id) for role in getattr(member, "roles", []))


async def _blocking_reason(interaction: discord.Interaction, config: dict) -> str | None:
    """Возвращает текст отказа, если пользователь сейчас не может подать анкету."""
    if not config.get("enabled", True):
        return "⛔ Приём анкет на этом сервере сейчас закрыт."

    approved_role_id = config.get("approved_role_id")
    if _has_role(interaction.user, approved_role_id):
        return "✅ Ваша анкета уже одобрена — доступ к серверу у вас есть."

    latest = await db_manager.get_latest_application(str(interaction.guild_id), str(interaction.user.id))
    if latest and latest.status == "pending":
        return "⏳ Ваша анкета уже на рассмотрении. Дождитесь решения администрации."
    if latest and latest.status == "approved" and not approved_role_id:
        return "✅ Ваша анкета уже одобрена."
    return None


class ApplicationModal(Modal):
    """Модальное окно с вопросами анкеты (вопросы настраиваются в веб-панели)."""

    def __init__(self, config: dict):
        super().__init__(title=_truncate(config.get("title") or "Анкета", 45))
        self.config = config
        self.questions = (config.get("questions") or [])[:MAX_MODAL_FIELDS]

        for question in self.questions:
            required = bool(question.get("required", True))
            max_length = max(1, min(int(question.get("max_length") or 1000), 4000))
            min_length = max(0, min(int(question.get("min_length") or 0), max_length)) if required else 0
            self.add_item(
                InputText(
                    label=_truncate(question.get("label") or "Вопрос", 45),
                    placeholder=_truncate(question.get("placeholder") or "", 100) or None,
                    style=(
                        discord.InputTextStyle.paragraph
                        if question.get("style") == "paragraph"
                        else discord.InputTextStyle.short
                    ),
                    required=required,
                    min_length=min_length,
                    max_length=max_length,
                )
            )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Повторная проверка: пока пользователь заполнял форму, он мог отправить её с другого окна
        reason = await _blocking_reason(interaction, self.config)
        if reason:
            await interaction.followup.send(reason, ephemeral=True)
            return

        user = interaction.user
        answers = [
            {"question": question.get("label") or "Вопрос", "answer": (field.value or "").strip()}
            for question, field in zip(self.questions, self.children)
        ]

        application_id = await db_manager.register_application(
            guild_id=str(interaction.guild_id),
            user_id=str(user.id),
            user_name=str(user),
            user_avatar=user.display_avatar.url if user.display_avatar else None,
            answers=answers,
        )

        await self._notify_reviewers(interaction, application_id, answers)

        await interaction.followup.send(
            "✅ Анкета отправлена! Администрация рассмотрит её в ближайшее время — "
            "о решении бот сообщит вам в личные сообщения.",
            ephemeral=True,
        )

    async def _notify_reviewers(self, interaction: discord.Interaction, application_id: str, answers: list):
        channel_id = self.config.get("review_channel_id")
        if not channel_id or not interaction.guild:
            return

        channel = interaction.guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return

        user = interaction.user
        embed = discord.Embed(
            title=f"📋 Новая анкета #{application_id}",
            description=f"От {user.mention} (`{user}`)\nРешение принимается в веб-панели.",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        for item in answers:
            embed.add_field(
                name=_truncate(item["question"], 256),
                value=_truncate(item["answer"] or "—", 1024),
                inline=False,
            )
        embed.set_footer(text="Статус: ⏳ на рассмотрении")

        try:
            message = await channel.send(embed=embed)
            await db_manager.set_application_review_message(application_id, str(channel.id), str(message.id))
        except discord.HTTPException:
            pass  # нет прав на канал — анкета всё равно сохранена и видна в панели


class ApplicationPanelView(View):
    """Постоянная панель с кнопкой подачи анкеты. Переживает перезапуск бота (custom_id + add_view)."""

    def __init__(self, button_label: str = "Заполнить анкету"):
        super().__init__(timeout=None)
        self.start_application.label = _truncate(button_label or "Заполнить анкету", 80)

    @button(
        label="Заполнить анкету",
        style=discord.ButtonStyle.success,
        emoji="📝",
        custom_id="application_start_btn",
    )
    async def start_application(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.guild:
            return

        config = await db_manager.get_application_config(str(interaction.guild_id))
        reason = await _blocking_reason(interaction, config)
        if reason:
            await interaction.response.send_message(reason, ephemeral=True)
            return

        await interaction.response.send_modal(ApplicationModal(config))


async def send_application_panel(ctx: discord.ApplicationContext):
    """Отправляет в текущий канал панель с кнопкой «Заполнить анкету»."""
    config = await db_manager.get_application_config(str(ctx.guild.id))

    embed = discord.Embed(
        title=config.get("title") or "📋 Анкета",
        description=config.get("description") or "",
        color=_parse_color(config.get("color")),
    )
    if config.get("banner_url"):
        embed.set_image(url=config["banner_url"])
    embed.set_footer(text="Нажмите кнопку ниже, чтобы заполнить анкету")

    await ctx.respond("Панель анкеты отправлена!", ephemeral=True)
    await ctx.channel.send(embed=embed, view=ApplicationPanelView(config.get("button_label")))
