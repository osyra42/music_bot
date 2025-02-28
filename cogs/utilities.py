import disnake
from disnake.ext import commands
import logging

logger = logging.getLogger(__name__)

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_ping(self):
        """Returns the bot's latency in milliseconds."""
        return round(self.bot.latency * 1000)

def setup(bot):
    bot.add_cog(Utilities(bot))