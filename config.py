# config.py
import os
import logging
import json
from rich.logging import RichHandler

# Replace these with your actual values
DISCORD_BOT_TOKEN = "***REMOVED***"
TEST_GUILD_IDS = [1328777698746564638]
LOGGING_LEVEL = logging.INFO

# Radio mode settings
# Get your NewsAPI key from https://newsapi.org/
NEWS_API_KEY = ""  # Add your NewsAPI key here

# TTS settings
TTS_PROVIDER = "gtts"  # Options: "gtts" (Google TTS) or "aws" (AWS Polly)

# AWS Polly settings (only needed if TTS_PROVIDER is "aws")
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
AWS_REGION = "us-east-1"

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("disnake")

# Load radio configuration
def load_radio_config():
    config_file = "radio_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading radio config: {e}")

    # Return default config if file doesn't exist or there's an error
    return {
        "tts_enabled": True,
        "news_enabled": True,
        "news_frequency": 5,
        "news_categories": ["technology", "general", "weather"],
        "host_personality": "friendly",
        "trivia_enabled": True,
        "time_based_content": True
    }
