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


class MyView(discord.ui.View):
    @discord.ui.select( # the decorator that lets you specify the properties of the select menu
        placeholder = "Choose a Flavor!", # the placeholder text that will be displayed if nothing is selected
        min_values = 1, # the minimum number of values that must be selected by the users
        max_values = 1, # the maximum number of values that can be selected by the users
        options = [ # the list of options from which users can choose, a required field
            discord.SelectOption(
                label="Vanilla",
                description="Pick this if you like vanilla!"
            ),
            discord.SelectOption(
                label="Chocolate",
                description="Pick this if you like chocolate!"
            ),
            discord.SelectOption(
                label="Strawberry",
                description="Pick this if you like strawberry!"
            )
        ]
    )
    async def select_callback(self, select, interaction): # the function called when the user is done selecting options
        await interaction.response.send_message(f"Awesome! I like {select.values[0]} too!")

@bot.slash_command(name = "sex2")
async def flavor(ctx):
    await ctx.respond("Choose a flavor!", view=MyView())


if __name__ == "__main__":
    bot.run(settings.BOT_TOKEN)

