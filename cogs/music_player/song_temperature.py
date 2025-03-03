import disnake
from disnake.ext import commands, tasks
import logging
import sqlite3
import random

logger = logging.getLogger("disnake")

class SongTemperature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_connection = sqlite3.connect('music_bot.db')
        self.db_cursor = self.db_connection.cursor()
        self.song_temperature_task.start()

    @tasks.loop(seconds=30)
    async def song_temperature_task(self):
        """Analyze user preferences and adjust the song temperature."""
        try:
            self.db_cursor.execute("""
                SELECT title, played, requested, skipped FROM song_stats
            """)
            songs = self.db_cursor.fetchall()

            if not songs:
                logger.warning("No song stats available.")
                return

            # Calculate song temperature based on user preferences
            song_temperature = {}
            for song in songs:
                title, played, requested, skipped = song
                temperature = (requested - skipped) / (played + 1)
                song_temperature[title] = temperature

            # Sort songs by temperature
            sorted_songs = sorted(song_temperature.items(), key=lambda x: x[1], reverse=True)

            # Select the next song based on temperature
            next_song = sorted_songs[0][0]
            logger.info(f"Selected next song based on temperature: {next_song}")

            # Add the selected song to the queue
            self.bot.get_cog('MusicPlayer').queue.append({"url": next_song, "user_id": self.bot.user.id})
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

    @song_temperature_task.before_loop
    async def before_song_temperature_task(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(SongTemperature(bot))
