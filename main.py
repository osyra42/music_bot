import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import random
import csv
import os
import logging
from typing import Dict, List, Optional, Any
#from dotenv import load_dotenv
from secret import YOUR_BOT_TOKEN_HERE

logging.basicConfig(level=logging.INFO)

#load_dotenv()
#TOKEN = os.getenv("DISCORD_TOKEN")

#if not TOKEN:
#    raise ValueError("DISCORD_TOKEN environment variable not set. Please create a .env file or set it manually.")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

PLAYLIST_FILE = 'playlist.csv'

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_states: Dict[int, Dict[str, Any]] = {}
        self.playlist_cache: List[Dict[str, str]] = self.load_playlist()
        self.auto_disconnect.start()

    def load_playlist(self) -> List[Dict[str, str]]:
        playlist = []
        try:
            with open(PLAYLIST_FILE, 'r', newline='', encoding='utf-8') as file:
                # Read the file and strip whitespace from fieldnames (column titles)
                reader = csv.DictReader(line.strip() for line in file)  # Strip entire line first
                reader.fieldnames = [name.strip() for name in reader.fieldnames]  # Normalize column names
                
                for i, row in enumerate(reader):
                    # Strip whitespace from values and check if required fields exist
                    url = row.get('url', '').strip()
                    title = row.get('title', '').strip()
                    artist = row.get('artist', '').strip()
                    
                    if url and title and artist:  # Only add if all fields are non-empty
                        playlist.append({
                            'url': url,
                            'title': title,
                            'artist': artist,
                            'track_number': i + 1
                        })
                    else:
                        logging.warning(f"Skipping incomplete row: {row}")
                        
            logging.info(f"Successfully loaded {len(playlist)} songs from {PLAYLIST_FILE}.")
            
        except FileNotFoundError:
            logging.warning(f"{PLAYLIST_FILE} not found. Creating an empty file.")
            with open(PLAYLIST_FILE, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['url', 'title', 'artist'])
        except Exception as e:
            logging.error(f"Error loading playlist: {e}")
        
        return playlist

    def get_guild_state(self, guild_id: int) -> Dict[str, Any]:
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = {
                'queue': asyncio.Queue(),
                'current_song': None,
                'is_playing': False,
                'play_next_song_task': None,
                'shuffled_playlist': [],
            }
        return self.guild_states[guild_id]
        
    def cog_unload(self):
        self.auto_disconnect.cancel()

    async def get_audio_info(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                return {
                    'stream_url': info['url'],
                    'title': info.get('title', 'Unknown Title'),
                    'uploader': info.get('uploader', 'Unknown Artist'),
                    'webpage_url': info.get('webpage_url', query),
                    'is_requested': True
                }
        except Exception as e:
            logging.error(f"Error fetching audio info for '{query}': {e}")
            return None

    def get_next_shuffled_song(self, guild_id: int) -> Optional[Dict[str, Any]]:
        if not self.playlist_cache:
            return None

        state = self.get_guild_state(guild_id)
        
        if not state['shuffled_playlist']:
            logging.info(f"Reshuffling playlist for guild {guild_id}.")
            new_shuffled_list = self.playlist_cache.copy()
            random.shuffle(new_shuffled_list)
            state['shuffled_playlist'] = new_shuffled_list

        if not state['shuffled_playlist']: # Still empty after trying to shuffle
            return None

        next_song = state['shuffled_playlist'].pop(0)

        return {
            'stream_url': next_song['url'],
            'title': next_song['title'],
            'uploader': next_song['artist'],
            'webpage_url': next_song['url'],
            'track_number': next_song['track_number'],
            'total_tracks': len(self.playlist_cache),
            'is_requested': False
        }

    async def play_next_song(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        state = self.get_guild_state(guild_id)
        
        if state['is_playing']:
            return

        if state['queue'].empty():
            shuffled_song = self.get_next_shuffled_song(guild_id)
            if not shuffled_song:
                state['is_playing'] = False
                return
            await state['queue'].put(shuffled_song)

        state['is_playing'] = True
        
        try:
            song_info = await state['queue'].get()
        except asyncio.CancelledError:
            state['is_playing'] = False
            return
            
        state['current_song'] = song_info
        
        if not song_info.get('is_requested', False):
            resolved_info = await self.get_audio_info(song_info['stream_url'])
            if not resolved_info:
                await ctx.send(f"⚠️ Could not resolve stream for **{song_info['title']}**. Skipping.")
                state['is_playing'] = False
                state['play_next_song_task'] = self.bot.loop.create_task(self.play_next_song(ctx))
                return
            song_info['stream_url'] = resolved_info['stream_url']

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song_info['stream_url'], **FFMPEG_OPTIONS), 
            volume=0.20
        )
        
        def after_playing(error):
            if error:
                logging.error(f'Playback error in guild {guild_id}: {error}')
            state['is_playing'] = False
            state['current_song'] = None
            state['play_next_song_task'] = self.bot.loop.create_task(self.play_next_song(ctx))

        if ctx.voice_client:
            ctx.voice_client.play(source, after=after_playing)
        else:
            state['is_playing'] = False
            return

        embed = discord.Embed(title="🎵 Now Playing", color=discord.Color.blue())
        if song_info.get('is_requested'):
            embed.description = f"[{song_info['title']}]({song_info['webpage_url']})\nby {song_info['uploader']}"
        else:
            embed.description = (f"Track {song_info['track_number']}/{song_info['total_tracks']}\n"
                               f"**[{song_info['title']}]({song_info['webpage_url']})** by **{song_info['uploader']}**")
        await ctx.send(embed=embed)

    @tasks.loop(seconds=60)
    async def auto_disconnect(self):
        for guild_id, state in list(self.guild_states.items()):
            guild = self.bot.get_guild(guild_id)
            if not guild:
                if guild_id in self.guild_states: del self.guild_states[guild_id]
                continue
            
            vc = guild.voice_client
            if vc and len(vc.channel.members) == 1:
                logging.info(f"Leaving empty channel in guild {guild.name}")
                await self.cleanup_guild_state(guild_id)

    @auto_disconnect.before_loop
    async def before_auto_disconnect(self):
        await self.bot.wait_until_ready()

    async def cleanup_guild_state(self, guild_id: int):
        state = self.get_guild_state(guild_id)
        guild = self.bot.get_guild(guild_id)

        if guild and guild.voice_client:
            await guild.voice_client.disconnect()
        
        if state['play_next_song_task']:
            state['play_next_song_task'].cancel()

        if guild_id in self.guild_states:
            del self.guild_states[guild_id]
        logging.info(f"Cleaned up state for guild {guild_id}")

    @commands.command(name='play', help='Plays a song from YouTube or a random track from the playlist.')
    async def play(self, ctx: commands.Context, *, query: Optional[str] = None):
        if not ctx.author.voice:
            return await ctx.send("🚫 You must be in a voice channel to use this command.")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        
        state = self.get_guild_state(ctx.guild.id)
        
        if query:
            await ctx.send(f"🔎 Searching for `{query}`...")
            song_info = await self.get_audio_info(query)
            if not song_info:
                return await ctx.send("⚠️ Could not find or process that song.")
            await state['queue'].put(song_info)
            await ctx.send(f"✅ Added to queue: **{song_info['title']}**")

        if not state['is_playing']:
            await self.play_next_song(ctx)
        elif not query:
             await ctx.send("🎶 A random song will play after the current queue is finished!")

    @commands.command(name='skip', help='Skips the current song.')
    async def skip(self, ctx: commands.Context):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("I'm not playing anything right now.")
        
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")

    @commands.command(name='stop', help='Stops playback, clears queue, and disconnects.')
    async def stop(self, ctx: commands.Context):
        if not ctx.voice_client:
            return await ctx.send("I'm not in a voice channel.")

        await self.cleanup_guild_state(ctx.guild.id)
        await ctx.send("⏹️ Stopped playback and cleared the queue.")

    @commands.command(name='queue', help='Shows the current song queue.')
    async def queue(self, ctx: commands.Context):
        state = self.get_guild_state(ctx.guild.id)
        
        if state['queue'].empty():
            return await ctx.send("The queue is empty. A random song will play next.")

        embed = discord.Embed(title="📜 Song Queue", color=discord.Color.purple())
        queue_list = list(state['queue']._queue)
        
        description = ""
        for i, song in enumerate(queue_list[:10]):
            description += f"{i+1}. **{song['title']}**\n"
        
        if len(queue_list) > 10:
            description += f"\n...and {len(queue_list) - 10} more."
            
        embed.description = description
        await ctx.send(embed=embed)
        
    @commands.command(name='current', aliases=['np'], help='Shows the currently playing song.')
    async def current(self, ctx: commands.Context):
        state = self.get_guild_state(ctx.guild.id)
        song_info = state.get('current_song')

        if not song_info:
            return await ctx.send("Nothing is currently playing.")

        embed = discord.Embed(title="🔊 Now Playing", color=discord.Color.green())
        if song_info.get('is_requested'):
            embed.description = f"[{song_info['title']}]({song_info['webpage_url']})\nby {song_info['uploader']}"
        else:
            embed.description = (f"Track {song_info['track_number']}/{song_info['total_tracks']}\n"
                               f"**[{song_info['title']}]({song_info['webpage_url']})** by **{song_info['uploader']}**")
        
        await ctx.send(embed=embed)

    @commands.command(name='addsong', help='Adds a song to the CSV playlist. Format: !addsong <url> <Title> by <Artist>')
    @commands.has_permissions(manage_guild=True)
    async def addsong(self, ctx: commands.Context, url: str, *, details: str):
        try:
            if " by " in details:
                title, artist = details.rsplit(" by ", 1)
            else:
                title = details
                artist = "Unknown Artist"

            url = url.strip()
            title = title.strip()
            artist = artist.strip()

            new_song = {
                'url': url,
                'title': title,
                'artist': artist,
                'track_number': len(self.playlist_cache) + 1
            }

            with open(PLAYLIST_FILE, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([url, title, artist])

            self.playlist_cache.append(new_song)
            await ctx.send(f"✅ Added **{title}** by **{artist}** to the playlist!\n*Note: It will be included in the next playlist shuffle cycle.*")

        except Exception as e:
            await ctx.send(f"⚠️ Error adding song: {e}. Please use the format `!addsong <url> <Title> by <Artist>`")

    @commands.command(name='showplaylist', help='Shows all songs in the predefined playlist.')
    async def showplaylist(self, ctx: commands.Context):
        if not self.playlist_cache:
            return await ctx.send("The playlist is empty.")

        embed = discord.Embed(title=f"🎵 Playlist ({len(self.playlist_cache)} songs)", color=discord.Color.gold())
        
        pages = []
        current_page = ""
        for song in self.playlist_cache:
            line = f"**{song['track_number']}.** {song['title']} by {song['artist']}\n"
            if len(current_page) + len(line) > 1024:
                pages.append(current_page)
                current_page = ""
            current_page += line
        pages.append(current_page)

        for i, page_content in enumerate(pages):
            embed.add_field(name=f"Page {i+1}", value=page_content, inline=False)
        
        await ctx.send(embed=embed)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')
    await bot.add_cog(MusicCog(bot))

bot.run(YOUR_BOT_TOKEN_HERE)
