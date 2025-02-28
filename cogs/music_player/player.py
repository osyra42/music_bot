import disnake
from disnake.ext import commands, tasks
import yt_dlp as youtube_dl
import asyncio
from datetime import timedelta
import logging
from cogs.utils.utils import MusicUtils
import os
import shutil
import random
from cogs.music_controls.controls import MusicControls

logger = logging.getLogger("disnake")

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

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_song = None
        self.progress_message = None
        self.progress_task = None
        self.queue = []  # List to store the queue of songs
        self.last_played = []  # List to store the last played songs
        self.voice_client = None  # Store the voice client for easier access
        self.playlist = []  # Store the shuffled playlist
        self.played_songs = []  # Store the songs that have been played
        self.cleanup_task.start()

    def create_media_embed(self, title, description, color=disnake.Color.blurple()):
        """Create a visually appealing embed for the media player."""
        try:
            embed = disnake.Embed(title=title, description=description, color=color)

            # Read the content from signature.txt
            try:
                with open('signature.txt', 'r') as file:
                    signature_text = file.read().strip()
                embed.set_footer(text=signature_text)
            except FileNotFoundError:
                logger.warning("signature.txt not found, skipping footer.")
            except Exception as e:
                logger.error(f"Error reading signature.txt: {e}", exc_info=True)

            embed.set_image(url=self.current_song.thumbnail if self.current_song
                            else "https://burgerbytestudio.com/favicon.png")
            return embed
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return disnake.Embed(title="Error", description=f"An error occurred: {str(e)}",
                                 color=disnake.Color.red())

    def create_progress_bar(self, total_duration: int, current_time: int) -> str:
        """
        Create a text-based progress bar with gradient color change.

        Args:
            total_duration (int): The total duration of the song in seconds.
            current_time (int): The current playback time in seconds.

        Returns:
            str: A string representing the progress bar.
        """
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
                    f"**[{self.current_song.title}]({self.current_song.url})**\n\n"
                    f"**Atrist:** {self.current_song.data.get('uploader') if self.current_song else 'Unknown'}\n\n"
                    f"**Requested by:** <@{inter.author.id}>"
                )
                embed.add_field(name="Progress", value=progress_bar, inline=False)

                queue_list = "\n".join([f"{i+1}. {song['title']}"
                                        for i, song in enumerate(self.queue[:10])])
                embed.add_field(name="Queue", value=queue_list, inline=False)

                if len(self.queue) > 10:
                    embed.add_field(name="See More",
                                    value="Click to see more songs in the queue", inline=False)

                if len(self.last_played) >= 2:
                    last_played_list = "\n".join([f"{i+1}. {song['title']}"
                                             for i, song in enumerate(self.last_played[-2:])])
                    embed.add_field(name="Last Played", value=last_played_list, inline=False)

                try:
                    await self.progress_message.edit(embed=embed)
                except disnake.NotFound:
                    break

                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            try:
                await inter.followup.send(f"An error occurred: {str(e)}")
            except disnake.HTTPException as http_e:
                logger.error(f"Failed to send followup message: {http_e}", exc_info=True)

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
                    f"**[{self.current_song.title}]({self.current_song.url})**\n\n"
                    f"**Duration:** {str(timedelta(seconds=self.current_song.duration))}\n"
                    f"**Requested by:** <@{next_song['user_id']}>"
                )

                progress_bar = self.create_progress_bar(self.current_song.duration, 0)
                embed.add_field(name="Progress", value=progress_bar, inline=False)

                queue_list = "\n".join([f"{i+1}. {song.get('title', 'Unknown Title')}"
                                        for i, song in enumerate(self.queue[:10])])
                embed.add_field(name="Queue", value=queue_list, inline=False)

                if len(self.queue) > 10:
                    embed.add_field(name="See More", value="Click to see more songs in the queue", inline=False)

                if len(self.last_played) >= 2:
                    last_played_list = "\n".join([f"{i+1}. {song.get('title', 'Unknown Title')}"
                                             for i, song in enumerate(self.last_played[-2:])])
                    embed.add_field(name="Last Played", value=last_played_list, inline=False)

                view = MusicControls(self.bot, self.queue, self.last_played)
                self.progress_message = await inter.followup.send(embed=embed, view=view)

                self.progress_task = self.bot.loop.create_task(self.update_progress(inter))
            else:
                logger.info("Attempting to parse playlist.txt...")
                try:
                    playlist = MusicUtils.parse_playlist("playlist.txt")
                    logger.info(f"Playlist parsed: {len(playlist['default'])} URLs found.")

                    if not playlist:
                        logger.warning("The playlist is empty.")
                        await inter.followup.send("The playlist is empty.")
                        return

                    all_songs = []
                    for section, songs in playlist.items():
                        all_songs.extend(songs)

                    if not self.playlist:
                        self.playlist = all_songs
                        random.shuffle(self.playlist)
                        self.played_songs = []

                    if not self.playlist:
                        logger.warning("No songs available in the playlist.")
                        await inter.followup.send("No songs available in the playlist.")
                        return

                    next_song = self.playlist.pop(0)
                    self.played_songs.append(next_song)

                    if len(self.played_songs) == len(all_songs):
                        logger.info("All songs have been played, reshuffling playlist.")
                        self.playlist = all_songs.copy()
                        random.shuffle(self.playlist)
                        self.played_songs = []

                    logger.info(f"Selected next song: {next_song}")
                    self.queue.append({"url": next_song['url'], "user_id": self.bot.user.id})
                    await self.play_next_song(inter)

                except FileNotFoundError:
                    logger.error("The playlist file (playlist.txt) was not found.")
                    await inter.followup.send("The playlist file (playlist.txt) was not found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.followup.send(f"An error occurred: {str(e)}")

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
        url = f"{url} explicit lyrics"
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
                f"**[{self.current_song.title}]({self.current_song.url})**\n\n"  # Clickable title
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

            self.progress_task = self.bot.loop.create_task(self.update_progress(inter))
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.followup.send(f"An error occurred: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_client_error(self, voice_client, error):
        """
        Handles voice client errors.

        Args:
            voice_client: The voice client instance.
            error: The error that occurred.
        """
        logger.error(f"Voice client error: {error}")
        if self.progress_task:
            self.progress_task.cancel()
        self.current_song = None
        self.progress_message = None
        self.queue.clear()

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Clean up downloaded music files every 24 hours."""
        music_pulls_dir = "music_pulls"
        if os.path.exists(music_pulls_dir):
            shutil.rmtree(music_pulls_dir)
        os.makedirs(music_pulls_dir)

def setup(bot):
    bot.add_cog(MusicPlayer(bot))
