import os
import disnake
from disnake.ext import commands
import logging
import secret

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"  # Simple log format
)

# Suppress disnake's verbose logging
logging.getLogger("disnake").setLevel(logging.WARNING)

# Bot setup
intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Function to dynamically load cogs
def load_cogs():
    cog_folder = "cogs"
    for filename in os.listdir(cog_folder):
        if filename.endswith(".py") and not filename.startswith("__"):
            cog_name = f"{cog_folder}.{filename[:-3]}"  # Remove .py extension
            try:
                bot.load_extension(cog_name)
                print(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                print(f"❌ Failed to load cog {cog_name}: {e}")

# Load cogs when the bot starts
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
    print("🔧 Loading cogs...")
    load_cogs()
    print("🚀 Cogs loaded and bot is ready!")

    # Check latency
    if hasattr(bot, 'latency') and bot.latency > 0:  # Ensure latency is available
        latency = round(bot.latency * 1000)
        print(f"⏱️ Bot is ready! Initial latency: {latency}ms")
    else:
        print("⚠️ Latency data not available during on_ready event.")

# Run the bot
if __name__ == "__main__":
    print("🚀 Starting Uta Yuki...")
    bot.run(secret.YOUR_BOT_TOKEN)