import discord
from app.settings import settings
from app.ticket_system import send_ticket_panel

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready")


@bot.slash_command(name="setup_ticket", description="Отправить панель создания тикетов")
async def setup_ticket(ctx: discord.ApplicationContext):
    await send_ticket_panel(ctx)

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

