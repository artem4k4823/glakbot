import logging

import discord
from app.settings import settings
from app.ticket_system import send_ticket_panel, TicketLaunchView, TicketCloseView
from app.application_system import send_application_panel, ApplicationPanelView

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

bot = discord.Bot()
_persistent_views_added = False


@bot.event
async def on_ready():
    global _persistent_views_added
    if not _persistent_views_added:
        # Регистрируем постоянные панели, чтобы кнопки на старых сообщениях работали после перезапуска
        bot.add_view(ApplicationPanelView())
        bot.add_view(TicketLaunchView(options=[]))
        bot.add_view(TicketCloseView())
        _persistent_views_added = True
    print(f"{bot.user} is ready")


@bot.slash_command(name="setup_ticket", description="Отправить панель создания тикетов")
async def setup_ticket(ctx: discord.ApplicationContext):
    # Сразу подтверждаем команду: у Discord лимит 3 сек на первый ответ, а сеть до API бывает медленной
    await ctx.defer(ephemeral=True)
    await send_ticket_panel(ctx)


@bot.slash_command(
    name="setup_application",
    description="Отправить в этот канал панель с анкетой для новых участников",
)
async def setup_application(ctx: discord.ApplicationContext):
    await ctx.defer(ephemeral=True)
    perms = ctx.channel.permissions_for(ctx.author) if ctx.guild else None
    if not perms or not (perms.administrator or perms.manage_guild):
        await ctx.respond("⛔ Команда доступна только администраторам сервера.", ephemeral=True)
        return
    await send_application_panel(ctx)


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    logging.exception("Ошибка в команде /%s", ctx.command.name if ctx.command else "?", exc_info=error)
    try:
        await ctx.respond(f"❌ Ошибка: {getattr(error, 'original', error)}", ephemeral=True)
    except discord.HTTPException:
        pass


@bot.event
async def on_interaction(interaction: discord.Interaction):
    from app.dashboard_service.manager import TicketDashboardManager
    db_manager = TicketDashboardManager()

    guild_id = str(interaction.guild_id) if interaction.guild_id else ""
    user_id = str(interaction.user.id)

    is_banned = await db_manager.check_ban(user_id=user_id, guild_id=guild_id)
    if is_banned:
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("⛔ Вы или этот сервер заблокированы администратором бота.", ephemeral=True)
        except Exception:
            pass
        return

    await bot.process_application_commands(interaction)


if __name__ == "__main__":
    bot.run(settings.BOT_TOKEN)
