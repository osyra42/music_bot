import disnake
from disnake.ext import commands
import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

logger = logging.getLogger("disnake")

class AdditionalSources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id='YOUR_SPOTIFY_CLIENT_ID',
            client_secret='YOUR_SPOTIFY_CLIENT_SECRET'
        ))

    @commands.slash_command(name="spotify_search", description="Search for a song on Spotify.")
    async def spotify_search(self, inter: disnake.ApplicationCommandInteraction, query: str):
        """Search for a song on Spotify."""
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                url = track['external_urls']['spotify']
                await inter.response.send_message(f"Found song: {track['name']} by {track['artists'][0]['name']}\nURL: {url}")
            else:
                await inter.response.send_message("No results found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(AdditionalSources(bot))
