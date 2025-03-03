import disnake
from disnake.ext import commands
import logging
import os

logger = logging.getLogger("disnake")

class PlaylistManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="add_to_playlist", description="Add a song to the playlist.")
    async def add_to_playlist(self, inter: disnake.ApplicationCommandInteraction, url: str):
        """Add a song to the playlist."""
        try:
            with open("playlist.txt", "a") as file:
                file.write(f"\n{url}")
            await inter.response.send_message(f"Added {url} to the playlist.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.slash_command(name="remove_from_playlist", description="Remove a song from the playlist.")
    async def remove_from_playlist(self, inter: disnake.ApplicationCommandInteraction, url: str):
        """Remove a song from the playlist."""
        try:
            with open("playlist.txt", "r") as file:
                lines = file.readlines()
            with open("playlist.txt", "w") as file:
                for line in lines:
                    if line.strip() != url:
                        file.write(line)
            await inter.response.send_message(f"Removed {url} from the playlist.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.slash_command(name="list_playlist", description="List all songs in the playlist.")
    async def list_playlist(self, inter: disnake.ApplicationCommandInteraction):
        """List all songs in the playlist."""
        try:
            with open("playlist.txt", "r") as file:
                playlist = file.readlines()
            playlist = [line.strip() for line in playlist]
            playlist_str = "\n".join(playlist)
            await inter.response.send_message(f"Playlist:\n{playlist_str}")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.slash_command(name="clear_playlist", description="Clear the playlist.")
    async def clear_playlist(self, inter: disnake.ApplicationCommandInteraction):
        """Clear the playlist."""
        try:
            with open("playlist.txt", "w") as file:
                file.write("")
            await inter.response.send_message("Playlist cleared.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(PlaylistManagement(bot))

    @commands.slash_command(name="add_to_playlist", description="Add a song to the playlist.")
    async def add_to_playlist(self, inter: disnake.ApplicationCommandInteraction, url: str):
        """Add a song to the playlist."""
        try:
            with open("playlist.txt", "a") as file:
                file.write(f"\n{url}")
            await inter.response.send_message(f"Added {url} to the playlist.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.slash_command(name="remove_from_playlist", description="Remove a song from the playlist.")
    async def remove_from_playlist(self, inter: disnake.ApplicationCommandInteraction, url: str):
        """Remove a song from the playlist."""
        try:
            with open("playlist.txt", "r") as file:
                lines = file.readlines()
            with open("playlist.txt", "w") as file:
                for line in lines:
                    if line.strip() != url:
                        file.write(line)
            await inter.response.send_message(f"Removed {url} from the playlist.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.slash_command(name="list_playlist", description="List all songs in the playlist.")
    async def list_playlist(self, inter: disnake.ApplicationCommandInteraction):
        """List all songs in the playlist."""
        try:
            with open("playlist.txt", "r") as file:
                playlist = file.readlines()
            playlist = [line.strip() for line in playlist]
            playlist_str = "\n".join(playlist)
            await inter.response.send_message(f"Playlist:\n{playlist_str}")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(PlaylistManagement(bot))
