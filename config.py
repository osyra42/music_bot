# config.py
import os
import logging
from rich.logging import RichHandler

with open('discord_bot_token.txt', 'r') as file:
    token = file.read().strip()
# Replace these with your actual values
DISCORD_BOT_TOKEN = str(token)
TEST_GUILD_IDS = [1193901642815377468]
LOGGING_LEVEL = logging.INFO

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("disnake")
