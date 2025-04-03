# cogs/radio/radio_mode.py
import disnake
from disnake.ext import commands, tasks
import asyncio
import logging
import random
import os
from datetime import datetime, timedelta
from .tts_engine import TTSEngine
from .news_fetcher import NewsFetcher
from .utils import RadioUtils
from cogs.music.utils import MusicUtils

logger = logging.getLogger("disnake")

class RadioMode(commands.Cog):
    """Radio mode cog for a radio-like music experience."""
    
    def __init__(self, bot):
        """Initialize the radio mode cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.tts_engine = TTSEngine()
        self.news_fetcher = NewsFetcher()
        self.config = RadioUtils.load_config()
        
        self.radio_active = False
        self.current_voice_client = None
        self.current_channel = None
        self.current_interaction = None
        
        self.playlist = []
        self.current_song = None
        self.songs_played = 0
        self.last_news_time = datetime.now() - timedelta(hours=1)  # Initialize to 1 hour ago
        
        self.cleanup_task.start()
        logger.info("Radio Mode cog initialized")
    
    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.cleanup_task.cancel()
    
    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Clean up cached files every 24 hours."""
        self.tts_engine.cleanup_cache()
        self.news_fetcher.cleanup_cache()
    
    @commands.slash_command(name="radio", description="Start radio mode with automated music and announcements")
    async def radio(self, inter: disnake.ApplicationCommandInteraction):
        """Start radio mode with automated music and announcements."""
        await inter.response.defer()
        
        # Check if the user is in a voice channel
        if not inter.author.voice:
            await inter.followup.send("You need to be in a voice channel to use radio mode.")
            return
        
        voice_channel = inter.author.voice.channel
        
        # Check if the bot is already in a voice channel
        if inter.guild.voice_client is not None:
            # If the bot is in a different channel, move it
            if inter.guild.voice_client.channel != voice_channel:
                await inter.guild.voice_client.disconnect()
                self.current_voice_client = await voice_channel.connect()
            else:
                self.current_voice_client = inter.guild.voice_client
        else:
            # Connect to the voice channel
            self.current_voice_client = await voice_channel.connect()
        
        # Stop any currently playing audio
        if self.current_voice_client.is_playing():
            self.current_voice_client.stop()
        
        # Reset radio state
        self.radio_active = True
        self.current_channel = inter.channel
        self.current_interaction = inter
        self.songs_played = 0
        
        # Load playlist
        await self._load_playlist()
        
        # Start with a greeting
        await self._play_greeting()
        
        # Start the radio
        await self._start_radio_loop()
    
    @commands.slash_command(name="stop_radio", description="Stop radio mode")
    async def stop_radio(self, inter: disnake.ApplicationCommandInteraction):
        """Stop radio mode."""
        if not self.radio_active:
            await inter.response.send_message("Radio mode is not active.")
            return
        
        await inter.response.defer()
        
        # Stop radio mode
        self.radio_active = False
        
        # Stop any currently playing audio
        if self.current_voice_client and self.current_voice_client.is_playing():
            self.current_voice_client.stop()
        
        # Disconnect from voice channel
        if self.current_voice_client:
            await self.current_voice_client.disconnect()
            self.current_voice_client = None
        
        await inter.followup.send("Radio mode stopped.")
    
    async def _load_playlist(self):
        """Load and shuffle the playlist."""
        try:
            # Parse the playlist file
            playlist_data = MusicUtils.parse_playlist("playlist.txt")
            
            # Flatten the playlist
            self.playlist = []
            for section in playlist_data.values():
                for item in section:
                    self.playlist.append(item)
            
            # Shuffle the playlist
            random.shuffle(self.playlist)
            
            logger.info(f"Loaded {len(self.playlist)} songs for radio mode")
        except Exception as e:
            logger.error(f"Error loading playlist: {e}", exc_info=True)
            self.playlist = []
    
    async def _play_greeting(self):
        """Play a time-appropriate greeting."""
        greeting = RadioUtils.get_time_of_day_greeting(self.config)
        
        if self.config.get("tts_enabled", True):
            try:
                # Generate TTS for the greeting
                greeting_file = await self.tts_engine.text_to_speech(greeting)
                
                if greeting_file and os.path.exists(greeting_file):
                    # Play the greeting
                    source = disnake.FFmpegPCMAudio(greeting_file)
                    self.current_voice_client.play(source, after=lambda e: self.bot.loop.create_task(self._after_greeting()))
                    
                    # Send a message
                    embed = disnake.Embed(
                        title="📻 Radio Mode",
                        description=f"**{greeting}**\n\nStarting radio mode...",
                        color=disnake.Color.blurple()
                    )
                    await self.current_interaction.followup.send(embed=embed)
                    return
            except Exception as e:
                logger.error(f"Error playing greeting: {e}", exc_info=True)
        
        # If TTS is disabled or there was an error, start the radio immediately
        await self._after_greeting()
    
    async def _after_greeting(self):
        """Called after the greeting is played."""
        if not self.radio_active:
            return
        
        # Play the first song
        await self._play_next_song()
    
    async def _play_next_song(self):
        """Play the next song in the playlist."""
        if not self.radio_active or not self.current_voice_client:
            return
        
        # Check if we need to play news
        if RadioUtils.should_play_news(self.songs_played, self.config):
            await self._play_news()
            return
        
        # Get the next song
        if not self.playlist:
            await self._load_playlist()
            
            if not self.playlist:
                logger.error("Failed to load playlist")
                await self.current_interaction.followup.send("Failed to load playlist. Stopping radio mode.")
                await self.stop_radio(self.current_interaction)
                return
        
        next_song = self.playlist.pop(0)
        self.current_song = next_song
        
        # Format song info
        song_info = {
            "url": next_song["url"],
            "title": next_song.get("description", "Unknown Song")
        }
        
        formatted_info = RadioUtils.format_song_info(song_info)
        
        # Play song introduction if TTS is enabled
        if self.config.get("tts_enabled", True) and self.config.get("trivia_enabled", True):
            try:
                # Get trivia about the song
                trivia = RadioUtils.get_song_trivia(formatted_info["title"], formatted_info["artist"])
                
                # Generate TTS for the introduction
                intro_file = await self.tts_engine.create_song_intro(
                    formatted_info["title"],
                    formatted_info["artist"],
                    trivia
                )
                
                if intro_file and os.path.exists(intro_file):
                    # Play the introduction
                    source = disnake.FFmpegPCMAudio(intro_file)
                    self.current_voice_client.play(source, after=lambda e: self.bot.loop.create_task(self._after_intro(song_info)))
                    
                    # Send a message
                    embed = disnake.Embed(
                        title="📻 Now Playing",
                        description=(
                            f"**{formatted_info['title']}** by **{formatted_info['artist']}**\n\n"
                            f"*{trivia}*"
                        ),
                        color=disnake.Color.blurple()
                    )
                    await self.current_channel.send(embed=embed)
                    return
            except Exception as e:
                logger.error(f"Error playing song introduction: {e}", exc_info=True)
        
        # If TTS is disabled or there was an error, play the song directly
        await self._play_song(song_info)
    
    async def _after_intro(self, song_info):
        """Called after the song introduction is played."""
        if not self.radio_active:
            return
        
        # Play the song
        await self._play_song(song_info)
    
    async def _play_song(self, song_info):
        """Play a song from YouTube."""
        if not self.radio_active or not self.current_voice_client:
            return
        
        try:
            # Import here to avoid circular imports
            from cogs.music.player import YTDLSource, ytdl
            
            # Get the song from YouTube
            song = await YTDLSource.from_url(song_info["url"], loop=self.bot.loop, stream=False)
            
            # Play the song
            self.current_voice_client.play(song, after=lambda e: self.bot.loop.create_task(self._after_song()))
            
            # Update song count
            self.songs_played += 1
            
            # Format song info
            formatted_info = RadioUtils.format_song_info(song_info)
            
            # Only send a message if we didn't already send one with the introduction
            if not (self.config.get("tts_enabled", True) and self.config.get("trivia_enabled", True)):
                embed = disnake.Embed(
                    title="📻 Now Playing",
                    description=f"**{formatted_info['title']}** by **{formatted_info['artist']}**",
                    color=disnake.Color.blurple()
                )
                embed.set_thumbnail(url=song.thumbnail)
                await self.current_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error playing song: {e}", exc_info=True)
            await self._after_song()  # Move to the next song
    
    async def _after_song(self):
        """Called after a song is finished playing."""
        if not self.radio_active:
            return
        
        # Play the next song
        await self._play_next_song()
    
    async def _play_news(self):
        """Play news updates."""
        if not self.radio_active or not self.current_voice_client:
            return
        
        # Reset song count
        self.songs_played = 0
        
        if not self.config.get("news_enabled", True):
            await self._play_next_song()
            return
        
        try:
            # Get news
            news_category = random.choice(self.config.get("news_categories", ["technology", "general"]))
            news_items = await self.news_fetcher.get_news(category=news_category)
            
            if not news_items:
                logger.warning(f"No news items found for category: {news_category}")
                await self._play_next_song()
                return
            
            # Generate TTS for the news
            if self.config.get("tts_enabled", True):
                news_file = await self.tts_engine.create_news_announcement(news_items, category=news_category)
                
                if news_file and os.path.exists(news_file):
                    # Play the news
                    source = disnake.FFmpegPCMAudio(news_file)
                    self.current_voice_client.play(source, after=lambda e: self.bot.loop.create_task(self._after_news()))
                    
                    # Send a message
                    embed = disnake.Embed(
                        title=f"📰 {news_category.capitalize()} News",
                        description="\n\n".join([f"**{item['title']}**\n{item['description']}" for item in news_items[:3]]),
                        color=disnake.Color.gold()
                    )
                    await self.current_channel.send(embed=embed)
                    return
            
            # If TTS is disabled or there was an error, just send the news and continue
            embed = disnake.Embed(
                title=f"📰 {news_category.capitalize()} News",
                description="\n\n".join([f"**{item['title']}**\n{item['description']}" for item in news_items[:3]]),
                color=disnake.Color.gold()
            )
            await self.current_channel.send(embed=embed)
            
            # Continue to the next song
            await self._play_next_song()
        except Exception as e:
            logger.error(f"Error playing news: {e}", exc_info=True)
            await self._play_next_song()
    
    async def _after_news(self):
        """Called after news is finished playing."""
        if not self.radio_active:
            return
        
        # Play the next song
        await self._play_next_song()
    
    async def _start_radio_loop(self):
        """Start the radio loop."""
        # The loop is driven by the after callbacks of the voice client
        # This method just starts the process
        if not self.radio_active:
            return
        
        # If we're not already playing something, start the first song
        if not self.current_voice_client.is_playing():
            await self._play_next_song()

def setup(bot):
    bot.add_cog(RadioMode(bot))
