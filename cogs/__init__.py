# cogs/music_cog.py
import disnake
from disnake.ext import commands, tasks
import yt_dlp as youtube_dl
import asyncio
from disnake import ui
from datetime import timedelta
import logging
import os
import shutil
import random

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'music_pulls/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # Bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

logger = logging.getLogger("disnake")

def parse_playlist(file_path):
    """
    Parses a custom playlist file with sections, URLs, and descriptions.
    """
    playlist = {}
    current_section = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Ignore comments and empty lines
            if line.startswith('#') or not line:
                continue
            # Check for section headers
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                playlist[current_section] = []
            else:
                # Split URL and description (if description exists)
                if ';' in line:
                    url, description = line.split(';', 1)
                else:
                    url, description = line, ''  # No description provided
                # Add to the current section
                playlist[current_section].append({
                    'url': url.strip(),
                    'description': description.strip()
                })

    return playlist

class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.start_time = asyncio.get_event_loop().time()

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(disnake.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicControls(ui.View):
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
            inter.guild.voice_client.play(self.bot.get_cog('Music').current_song, after=lambda e: self.bot.loop.create_task(self.bot.get_cog('Music').on_song_end(inter)))
            embed = disnake.Embed(title="Music Controls", description="🔄 Replayed the current song.", color=0x00ff00)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_song = None
        self.progress_message = None
        self.progress_task = None
        self.queue = []  # List to store the queue of songs
        self.last_played = []  # List to store the last played songs
        self.voice_client = None  # Store the voice client for easier access
        self.cleanup_task.start()

    def create_media_embed(self, title, description, color=disnake.Color.blurple()):
        """Create a visually appealing embed for the media player."""
        try:
            embed = disnake.Embed(
                title=title,
                description=description,
                color=color,
            )
            embed.set_thumbnail(url=self.current_song.thumbnail if self.current_song else "https://burgerbytestudio.com/favicon.png")
            # Read the content from signature.txt
            with open('signature.txt', 'r') as file:
                signature_text = file.read().strip()

            # Use the text from signature.txt in the embed footer
            embed.set_footer(text=signature_text)
            embed.set_image(url=self.current_song.thumbnail if self.current_song else "https://burgerbytestudio.com/favicon.png")
            embed.set_author(name=self.current_song.title if self.current_song else "No song playing", icon_url=self.current_song.thumbnail if self.current_song else "https://burgerbytestudio.com/favicon.png")
            embed.add_field(name="Artist", value=self.current_song.data.get('uploader') if self.current_song else "Unknown", inline=True)

            # Add progress bar
            progress_bar = self.create_progress_bar(self.current_song.duration, 0)
            embed.add_field(name="Progress", value=progress_bar, inline=False)

            # Add queue list
            queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queue[:10])])
            embed.add_field(name="Queue", value=queue_list, inline=False)

            # Add "See More" option
            if len(self.queue) > 10:
                embed.add_field(name="See More", value="Click to see more songs in the queue", inline=False)

            # Add last two played songs
            if len(self.last_played) >= 2:
                last_played_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.last_played[-2:])])
                embed.add_field(name="Last Played", value=last_played_list, inline=False)

            return embed
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return disnake.Embed(title="Error", description=f"An error occurred: {str(e)}", color=disnake.Color.red())

    def create_progress_bar(self, total_duration: int, current_time: int) -> str:
        """Create a text-based progress bar with gradient color change."""
        try:
            progress = int((current_time / total_duration) * 20)  # 20 characters for the progress bar
            gradient = int((current_time / total_duration) * 255)  # Gradient from green to red
            color = f"{255 - gradient:02x}{gradient:02x}00"  # Green to red gradient
            return f"`{'█' * progress}{'░' * (20 - progress)}` {timedelta(seconds=current_time)} / {timedelta(seconds=total_duration)}"
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return f"An error occurred: {str(e)}"

    async def update_progress(self, inter: disnake.ApplicationCommandInteraction):
        """Update the progress bar in the embed every second."""
        try:
            while self.current_song and inter.guild.voice_client and inter.guild.voice_client.is_playing():
                current_time = int(asyncio.get_event_loop().time() - self.current_song.start_time)

                progress_bar = self.create_progress_bar(self.current_song.duration, current_time)

                embed = self.create_media_embed(
                    "🎶 Now Playing",
                    f"**{self.current_song.title}**\n\n"
                    f"**Duration:** {str(timedelta(seconds=self.current_song.duration))}\n"
                    f"**Requested by:** <@{inter.author.id}>"
                )
                embed.add_field(name="Progress", value=progress_bar, inline=False)

                # Add queue list to the embed
                queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queue[:10])])
                embed.add_field(name="Queue", value=queue_list, inline=False)

                # Add "See More" option to the embed
                if len(self.queue) > 10:
                    embed.add_field(name="See More", value="Click to see more songs in the queue", inline=False)

                # Add last two played songs to the embed
                if len(self.last_played) >= 2:
                    last_played_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.last_played[-2:])])
                    embed.add_field(name="Last Played", value=last_played_list, inline=False)

                try:
                    await self.progress_message.edit(embed=embed)
                except disnake.NotFound:
                    break  # Stop updating if the message is deleted

                await asyncio.sleep(1)  # Update every 1 second
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.followup.send(f"An error occurred: {str(e)}")

    async def play_next_song(self, inter: disnake.ApplicationCommandInteraction):
        """Play the next song in the queue."""
        try:
            if self.queue:
                next_song = self.queue.pop(0)  # Get the next song from the queue
                self.current_song = await YTDLSource.from_url(next_song['url'], loop=self.bot.loop, stream=False)

                if inter.guild.voice_client is None:
                    logger.error("I'm not connected to a voice channel.")
                    await inter.followup.send("I'm not connected to a voice channel.")
                    return

                logger.info(f"Playing next song: {self.current_song.title}")
                inter.guild.voice_client.play(self.current_song, after=lambda e: self.bot.loop.create_task(self.on_song_end(inter)))

                # Create a media player embed
                embed = self.create_media_embed(
                    "🎶 Now Playing",
                    f"**{self.current_song.title}**\n\n"
                    f"**Duration:** {str(timedelta(seconds=self.current_song.duration))}\n"
                    f"**Requested by:** <@{next_song['user_id']}>"
                )

                # Add a progress bar
                progress_bar = self.create_progress_bar(self.current_song.duration, 0)
                embed.add_field(name="Progress", value=progress_bar, inline=False)

                # Add queue list to the embed
                queue_list = "\n".join([f"{i+1}. {song.get('title', 'Unknown Title')}" for i, song in enumerate(self.queue[:10])])
                embed.add_field(name="Queue", value=queue_list, inline=False)

                # Add "See More" option to the embed
                if len(self.queue) > 10:
                    embed.add_field(name="See More", value="Click to see more songs in the queue", inline=False)

                # Add last two played songs to the embed
                if len(self.last_played) >= 2:
                    last_played_list = "\n".join([f"{i+1}. {song.get('title', 'Unknown Title')}" for i, song in enumerate(self.last_played[-2:])])
                    embed.add_field(name="Last Played", value=last_played_list, inline=False)

                # Send the embed with music controls
                view = MusicControls(self.bot, self.queue, self.last_played)  # Pass queue and last_played
                self.progress_message = await inter.followup.send(embed=embed, view=view)

                # Start the progress update task
                self.progress_task = self.bot.loop.create_task(self.update_progress(inter))
            else:
                # No more songs in the queue, play a random song from the parsed playlist
                logger.info("Attempting to parse playlist.txt...")
                playlist = parse_playlist("playlist.txt")  # Parse the playlist file
                logger.info(f"Playlist parsed: {playlist}")

                if playlist:
                    # Flatten the playlist into a list of URLs
                    all_songs = []
                    for section, songs in playlist.items():
                        all_songs.extend(songs)

                    logger.info(f"All songs in playlist: {all_songs}")

                    if all_songs:
                        random_song = random.choice(all_songs)
                        logger.info(f"Selected random song: {random_song}")
                        self.queue.append({"url": random_song['url'], "user_id": self.bot.user.id})
                        await self.play_next_song(inter)
                    else:
                        logger.warning("No songs available in the playlist.")
                        await inter.followup.send("No songs available in the playlist.")
                else:
                    logger.warning("The playlist is empty.")
                    await inter.followup.send("The playlist is empty.")
        except FileNotFoundError:
            logger.error("The playlist file (playlist.txt) was not found.")
            await inter.followup.send("The playlist file (playlist.txt) was not found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)  # Log the full exception traceback
            await inter.followup.send(f"An error occurred: {str(e)}")  # Ensure the error message is displayed

        # No more songs in the queue, disconnect after a delay
        await asyncio.sleep(60)  # Wait 60 seconds before disconnecting
        if not inter.guild.voice_client.is_playing() and not self.queue:
            await inter.guild.voice_client.disconnect()
            self.current_song = None

    async def on_song_end(self, inter: disnake.ApplicationCommandInteraction):
        """Handle the end of a song."""
        try:
            if self.progress_task:
                self.progress_task.cancel()  # Stop the progress update task
            self.last_played.append(self.current_song.data)  # Add the current song to the last played list

            if inter.guild.voice_client is None:
                logger.error("I'm not connected to a voice channel.")
                await inter.followup.send("I'm not connected to a voice channel.")
                return

            logger.info(f"Song ended: {self.current_song.title}")
            await self.play_next_song(inter)  # Play the next song in the queue
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.followup.send(f"An error occurred: {str(e)}")

    @commands.slash_command(name="play", description="Play a song from YouTube.")
    async def play(self, inter: disnake.ApplicationCommandInteraction, url: str):
        """Play a song from YouTube."""
        await inter.response.defer()

        try:
            if not inter.author.voice:
                logger.error("User is not connected to a voice channel.")
                await inter.followup.send("You are not connected to a voice channel.")
                return

            voice_channel = inter.author.voice.channel

            # Connect to the voice channel if not already connected
            if inter.guild.voice_client is None:
                logger.info(f"Connecting to voice channel: {voice_channel.name}")
                self.voice_client = await voice_channel.connect()
            elif inter.guild.voice_client.channel != voice_channel:
                logger.info(f"Moving to voice channel: {voice_channel.name}")
                await inter.guild.voice_client.move_to(voice_channel)

            # Ensure the bot is connected to the voice channel
            if inter.guild.voice_client is None or not inter.guild.voice_client.is_connected():
                logger.error("Failed to connect to the voice channel.")
                await inter.followup.send("Failed to connect to the voice channel.")
                return

            # If the bot is already playing a song, add the new song to the queue
            if inter.guild.voice_client.is_playing():
                logger.info(f"Adding song to queue: {url}")
                self.queue.append({"url": url, "user_id": inter.author.id})
                await inter.followup.send(f"Added to queue: {url}")
                return

            # Play the requested song
            self.current_song = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)

            if inter.guild.voice_client is None:
                logger.error("I'm not connected to a voice channel.")
                await inter.followup.send("I'm not connected to a voice channel.")
                return

            logger.info(f"Playing song: {self.current_song.title}")
            inter.guild.voice_client.play(self.current_song, after=lambda e: self.bot.loop.create_task(self.on_song_end(inter)))

            # Create a media player embed
            embed = self.create_media_embed(
                "🎶 Now Playing",
                f"**{self.current_song.title}**\n\n"
                f"**Duration:** {str(timedelta(seconds=self.current_song.duration))}\n"
                f"**Requested by:** <@{inter.author.id}>"
            )

            # Add a progress bar
            progress_bar = self.create_progress_bar(self.current_song.duration, 0)
            embed.add_field(name="Progress", value=progress_bar, inline=False)

            # Add queue list to the embed
            queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queue[:10])])
            embed.add_field(name="Queue", value=queue_list, inline=False)

            # Add "See More" option to the embed
            if len(self.queue) > 10:
                embed.add_field(name="See More", value="Click to see more songs in the queue", inline=False)

            # Add last two played songs to the embed
            if len(self.last_played) >= 2:
                last_played_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.last_played[-2:])])
                embed.add_field(name="Last Played", value=last_played_list, inline=False)

            # Send the embed with music controls
            view = MusicControls(self.bot, self.queue, self.last_played)  # Pass queue and last_played
            self.progress_message = await inter.followup.send(embed=embed, view=view)

            # Start the progress update task
            self.progress_task = self.bot.loop.create_task(self.update_progress(inter))
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.followup.send(f"An error occurred: {str(e)}")

    # Removed the disconnect method

    # Removed the on_voice_state_update method

    # Removed the on_voice_client_disconnect and on_voice_client_error methods

    @commands.Cog.listener()
    async def on_voice_client_error(self, voice_client, error):
        """Handle voice client errors."""
        logger.error(f"Voice client error: {error}")
        if self.progress_task:
            self.progress_task.cancel()  # Stop the progress update task
        self.current_song = None
        self.progress_message = None
        self.queue.clear()

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Clean up downloaded music files every 24 hours."""
        if os.path.exists("music_pulls"):
            shutil.rmtree("music_pulls")
        os.makedirs("music_pulls")

def setup(bot):
    bot.add_cog(Music(bot))