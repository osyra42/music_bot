import disnake
from disnake import ui
import logging
from disnake.ext import commands

logger = logging.getLogger("disnake")

class MusicControls(commands.Cog, ui.View):
    def __init__(self, bot, queue, last_played):
        super().__init__(timeout=None)
        self.bot = bot
        self.queue = queue  # Pass the queue from the Music cog
        self.last_played = last_played  # Pass the last_played list from the Music cog

    @ui.button(label="⏸️ Pause", style=disnake.ButtonStyle.secondary)
    async def pause_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_playing():
                await inter.response.send_message("No song is currently playing.", ephemeral=True)
                return

            inter.guild.voice_client.pause()
            embed = disnake.Embed(title="Music Controls", description="⏸️ Paused the current song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="▶️ Resume", style=disnake.ButtonStyle.secondary)
    async def resume_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_paused():
                await inter.response.send_message("No song is currently paused.", ephemeral=True)
                return

            inter.guild.voice_client.resume()
            embed = disnake.Embed(title="Music Controls", description="▶️ Resumed the current song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="⏭️ Skip", style=disnake.ButtonStyle.secondary)
    async def skip_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_playing():
                await inter.response.send_message("No song is currently playing.", ephemeral=True)
                return

            inter.guild.voice_client.stop()
            embed = disnake.Embed(title="Music Controls", description="⏭️ Skipped the current song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="⏹️ Stop", style=disnake.ButtonStyle.danger)
    async def stop_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None:
                await inter.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
                return

            inter.guild.voice_client.stop()
            await inter.guild.voice_client.disconnect()
            embed = disnake.Embed(title="Music Controls", description="⏹️ Stopped the music and disconnected.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="⏮️ Previous", style=disnake.ButtonStyle.secondary)
    async def previous_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_playing():
                await inter.response.send_message("No song is currently playing.", ephemeral=True)
                return

            # Check if there are any previously played songs
            if not self.last_played:
                await inter.response.send_message("No previous song to play.", ephemeral=True)
                return

            # Get the last played song and add it back to the queue
            previous_song = self.last_played.pop()
            self.queue.insert(0, previous_song)

            # Stop the current song and play the previous one
            inter.guild.voice_client.stop()
            embed = disnake.Embed(title="Music Controls", description="⏮️ Playing the previous song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="🔊 Volume", style=disnake.ButtonStyle.secondary)
    async def volume_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None:
                await inter.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
                return

            # Implement volume control logic here
            if inter.guild.voice_client is None:
                await inter.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
                return

            # Normalize the volume to 50%
            inter.guild.voice_client.source.volume = 0.05
            embed = disnake.Embed(title="Music Controls", description="🔊 Adjusted the volume.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @ui.button(label="🔄 Replay", style=disnake.ButtonStyle.secondary)
    async def replay_button(self, button: ui.Button, inter: disnake.Interaction):
        try:
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_playing():
                await inter.response.send_message("No song is currently playing.", ephemeral=True)
                return

            # Replay the current song
            inter.guild.voice_client.stop()
            inter.guild.voice_client.play(self.bot.get_cog('music').current_song, after=lambda e: self.bot.loop.create_task(self.bot.get_cog('music').on_song_end(inter)))
            embed = disnake.Embed(title="Music Controls", description="🔄 Replayed the current song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(MusicControls(bot, queue=None, last_played=None))