import discord
from discord.ui import Modal, InputText, View, button, Select, select
import datetime
from app.dashboard_service.manager import TicketDashboardManager

db_manager = TicketDashboardManager()


def create_ticket_option(
    label: str,
    description: str = "",
    emoji: str | None = None,
    value: str | None = None
) -> discord.SelectOption:
    return discord.SelectOption(
        label=label,
        description=description,
        emoji=emoji,
        value=value or label
    )


class TicketCloseView(View):
    """Панель управления внутри созданного тикета."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(
        label="Закрыть тикет",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket_close_btn"
    )
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🔒 Тикет будет закрыт и удален через 5 секунд...",
            ephemeral=True
        )
        channel = interaction.channel
        guild = interaction.guild

        if channel and guild:
            await db_manager.update_ticket_status(guild_id=str(guild.id), channel_id=str(channel.id), status="closed")

        await discord.utils.sleep_until(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=5))
        if channel:
            await channel.delete(reason=f"Тикет закрыт пользователем {interaction.user}")


class TicketModal(Modal):
    """Модальное окно для ввода информации при создании тикета."""
    def __init__(self, category: str = "Общие вопросы"):
        super().__init__(title="📩 Создание тикета поддержки")
        self.ticket_category = category

        self.add_item(
            InputText(
                label="Тема обращения",
                placeholder="Кратко опишите причину обращения...",
                min_length=3,
                max_length=100,
                required=True
            )
        )
        self.add_item(
            InputText(
                label="Подробное описание",
                placeholder="Укажите все детали вашего вопроса или проблемы...",
                style=discord.InputTextStyle.paragraph,
                min_length=10,
                max_length=1000,
                required=True
            )
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        subject = self.children[0].value
        description = self.children[1].value

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            user: discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True, manage_channels=True)
        }

        config = await db_manager.get_panel_embed_data(str(guild.id))
        admin_role_ids = config.get("admin_role_ids", [])
        for role_id in admin_role_ids:
            try:
                role = guild.get_role(int(role_id))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True)
            except ValueError:
                pass

        category_name = "Тикеты поддержки"
        ticket_category_obj = discord.utils.get(guild.categories, name=category_name)
        if not ticket_category_obj:
            ticket_category_obj = await guild.create_category(name=category_name)

        channel_name = f"ticket-{user.name}".lower().replace(" ", "-")
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category_obj,
            overwrites=overwrites,
            reason=f"Тикет от {user}"
        )

        ticket_id = await db_manager.register_ticket(
            guild_id=str(guild.id),
            user_name=str(user),
            user_id=str(user.id),
            category=self.ticket_category,
            subject=subject,
            description=description,
            channel_id=str(ticket_channel.id)
        )

        embed = discord.Embed(
            title=f"🎫 Тикет #{ticket_id}: {subject}",
            description="Спасибо за обращение в поддержку! Администрация ответит вам в ближайшее время.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="👤 Автор", value=user.mention, inline=True)
        embed.add_field(name="📂 Категория", value=self.ticket_category, inline=True)
        embed.add_field(name="📝 Описание проблемы", value=description, inline=False)
        embed.set_footer(text="Нажмите кнопку ниже для закрытия тикета", icon_url=user.display_avatar.url)

        await ticket_channel.send(
            content=f"{user.mention} | Администрация",
            embed=embed,
            view=TicketCloseView()
        )

        await interaction.followup.send(
            f"✅ Ваш тикет `{ticket_id}` успешно создан: {ticket_channel.mention}",
            ephemeral=True
        )


class TicketSelect(Select):
    """Выпадающее меню для выбора категории тикета."""
    def __init__(self, options: list[discord.SelectOption], placeholder: str = "Выберите категорию обращения..."):
        if not options:
            options = [discord.SelectOption(label="Общие вопросы", emoji="❓")]
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            custom_id="ticket_category_select",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        modal = TicketModal(category=selected_category)
        await interaction.response.send_modal(modal)


class TicketLaunchView(View):
    """Красивая интерактивная панель создания тикета с поддержкой динамических категорий из дашборда."""
    def __init__(self, options: list[discord.SelectOption], placeholder: str = "Выберите категорию обращения..."):
        super().__init__(timeout=None)
        self.add_item(TicketSelect(options=options, placeholder=placeholder))

    @button(
        label="Быстрый тикет",
        style=discord.ButtonStyle.success,
        emoji="📩",
        custom_id="ticket_quick_create_btn"
    )
    async def quick_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = TicketModal(category="Общие вопросы")
        await interaction.response.send_modal(modal)


async def send_ticket_panel(
    ctx: discord.ApplicationContext,
    placeholder: str = "Выберите категорию обращения..."
):
    """Основная функция для отправки красивого интерфейса тикет-системы в канал."""
    guild_id = str(ctx.guild.id)
    config = await db_manager.get_panel_embed_data(guild_id)
    options = await db_manager.get_ticket_options(guild_id)

    hex_color = config.get("color", "#5865F2").lstrip("#")
    try:
        color_int = int(hex_color, 16)
    except ValueError:
        color_int = 0x5865F2

    embed = discord.Embed(
        title=config.get("title", "🎫 Поддержка и обратная связь"),
        description=config.get("description", "Добро пожаловать в центр поддержки!"),
        color=discord.Color(color_int)
    )
    
    banner_url = config.get("banner_url")
    if banner_url:
        embed.set_image(url=banner_url)

    footer_text = config.get("footer_text", "Служба поддержки")
    embed.set_footer(text=footer_text)

    view = TicketLaunchView(options=options, placeholder=placeholder)
    await ctx.respond("Панель тикетов отправлена!", ephemeral=True)
    await ctx.channel.send(embed=embed, view=view)
