# config.py
import os
import logging
from rich.logging import RichHandler

# Replace these with your actual values
DISCORD_BOT_TOKEN = "***REMOVED***"
TEST_GUILD_IDS = [1328777698746564638]
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
