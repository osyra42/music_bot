import disnake
from disnake.ext import commands, tasks
import logging
import random
import asyncio
import requests

logger = logging.getLogger("disnake")

class RadioHostMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.radio_host_task.start()

    @tasks.loop(seconds=30)
    async def radio_host_task(self):
        """Simulate a radio host introducing songs and providing commentary."""
        try:
            if not self.bot.voice_clients:
                logger.info("No voice clients connected.")
                return

            voice_client = self.bot.voice_clients[0]
            if not voice_client.is_playing():
                logger.info("No song is currently playing.")
                return

            # Introduce the song with commentary
            current_song = self.bot.get_cog('MusicPlayer').current_song
            if current_song:
                await voice_client.send(f"Now playing: {current_song.title} by {current_song.data.get('uploader')}")

                # Fetch and read news updates
                news = self.fetch_news()
                if news:
                    await voice_client.send(f"Breaking news: {news}")

                # Provide fun facts or trivia
                fun_fact = self.get_fun_fact()
                if fun_fact:
                    await voice_client.send(f"Did you know? {fun_fact}")

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

    def fetch_news(self):
        """Fetch news updates from a public API."""
        try:
            response = requests.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_NEWS_API_KEY")
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                if articles:
                    return articles[0].get('title')
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching news: {e}", exc_info=True)
            return None

    def get_fun_fact(self):
        """Provide a fun fact or trivia."""
        fun_facts = [
            "Did you know that a day on Venus is longer than a year on Venus?",
            "The shortest war in history lasted only 38-45 minutes.",
            "Octopuses have three hearts.",
            "A group of flamingos is called a 'flamboyance'."
        ]
        return random.choice(fun_facts)

    @radio_host_task.before_loop
    async def before_radio_host_task(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(RadioHostMode(bot))
