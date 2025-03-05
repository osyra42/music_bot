# bot.py
import disnake
from disnake.ext import commands
import logging
from secret import setup_logging, TEST_GUILD_IDS
from utils.cog_manager import load_cogs
from secret import setup_logging, TEST_GUILD_IDS, DISCORD_BOT_TOKEN

logger = setup_logging()

intents = disnake.Intents.default()
intents.message_content = True  # Enable the message content intent

bot = commands.Bot(
    command_prefix="~",  # Fallback prefix for legacy commands
    intents=intents,
    help_command=None,  # Disable the default help command
    case_insensitive=True,  # Make commands case-insensitive
    test_guilds=TEST_GUILD_IDS,  # Specify the guild IDs for slash commands as a list of integers
)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("------")

    load_cogs(bot)  # Load all cogs

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
