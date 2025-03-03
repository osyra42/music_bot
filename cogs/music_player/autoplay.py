import disnake
from disnake.ext import commands, tasks
import random
import logging
from cogs.music_player.player import MusicPlayer

logger = logging.getLogger("disnake")

class Autoplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_player = MusicPlayer(bot)
        self.autoplay_task.start()

    @tasks.loop(seconds=30)
    async def autoplay_task(self):
        """Automatically play a song from the playlist if no requests have been made."""
        if not self.music_player.queue and not self.music_player.current_song:
            logger.info("No requests made, playing a song from the playlist.")
            await self.music_player.play_next_song(None)

    @autoplay_task.before_loop
    async def before_autoplay_task(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Autoplay(bot))
