import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random
import csv
from secret import YOUR_BOT_TOKEN_HERE

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Single queue for the bot
song_queue = asyncio.Queue()
current_track_number = 0

# YouTube DL configuration
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'extract_flat': True,
    'noplaylist': True,
    'socket_timeout': 10
}

# FFmpeg audio options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

def strip_whitespace(row):
    """Strip whitespace from all elements in a row"""
    return [item.strip() if isinstance(item, str) else item for item in row]

async def get_random_song():
    """Get a random song from the playlist by counting rows and selecting a random one"""
    try:
        with open('playlist.csv', 'r', newline='', encoding='utf-8') as csvfile:
            # Count rows (excluding header)
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            rows = [strip_whitespace(row) for row in reader if row]  # Read and clean all rows
            row_count = len(rows)
            
            if row_count <= 0:
                return None, 0
                
            # Choose random track number
            track_num = random.randint(1, row_count)
            selected_row = rows[track_num - 1]
            
            if len(selected_row) >= 3:  # If CSV has url, title, artist
                return {
                    'url': selected_row[0],
                    'title': selected_row[1],
                    'artist': selected_row[2],
                    'track_number': track_num
                }, row_count
            else:  # If just URL
                return {
                    'url': selected_row[0],
                    'title': 'Unknown Track',
                    'artist': 'Unknown Artist',
                    'track_number': track_num
                }, row_count
    except Exception as e:
        print(f"Error getting random song: {e}")
        return None, 0

async def get_audio_info(query, is_requested=False):
    """Extract audio information from YouTube"""
    if is_requested:
        with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:  # Handle playlists/search results
                    info = info['entries'][0]
                
                return {
                    'url': info['url'],
                    'title': info.get('title', 'Unknown Track'),
                    'artist': 'Unknown Artist',
                    'is_requested': True,
                    'track_number': 0  # 0 indicates it's a requested song, not from playlist
                }
            except Exception as e:
                print(f"Error getting audio info: {e}")
                return None
    else:
        # For random songs from playlist
        song_info, total_tracks = await get_random_song()
        if song_info:
            song_info['total_tracks'] = total_tracks
            song_info['is_requested'] = False
            return song_info
        else:
            return None

async def play_random_song(ctx):
    """Play a random song from playlist"""
    audio_info = await get_audio_info("", is_requested=False)
    
    if not audio_info:
        await ctx.send("⚠️ Couldn't load a random song. The playlist might be empty!")
        return
    
    await song_queue.put(audio_info)
    await play_next(ctx)

async def play_next(ctx):
    """Play the next song in queue at fixed 20% volume"""
    if not ctx.voice_client:
        return

    if song_queue.empty():
        await play_random_song(ctx)
        return

    audio_info = await song_queue.get()
    
    if not audio_info:
        await play_next(ctx)  # Silent failover
        return

    try:
        def after_playing(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(audio_info['url'], download=False)
            if 'entries' in info:
                info = info['entries'][0]
            audio_url = info['url']

        # Fixed 20% volume implementation
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
            volume=0.15
        )
        
        ctx.voice_client.play(source, after=after_playing)
        
        # Original track announcement (without volume mention)
        if audio_info.get('is_requested', False):
            await ctx.send(f"🎵 Now playing: **{audio_info['title']}**")
        else:
            await ctx.send(
                f"🎵 Now playing track {audio_info['track_number']}/{audio_info.get('total_tracks', '?')} — "
                f"**{audio_info['title']}** by **{audio_info['artist']}**"
            )
            
    except Exception as e:
        print(f"Playback error: {e}")
        await play_next(ctx)  # Silent recovery

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # Start the background task for checking empty voice channels
    bot.loop.create_task(check_empty_voice_channels())

async def check_empty_voice_channels():
    """Background task to check for empty voice channels"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(60)  # Check every 60 seconds
        
        for voice_client in bot.voice_clients:
            # Check if there's only the bot in the voice channel
            if len(voice_client.channel.members) == 1:
                await voice_client.disconnect()
                song_queue = asyncio.Queue()  # Clear the queue
                print("Left voice channel due to inactivity")

@bot.command()
async def play(ctx, *, query=None):
    """Play a song or random track"""
    if not ctx.author.voice:
        return await ctx.send("🚫 You must be in a voice channel!")

    # Connect to voice channel
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        await ctx.voice_client.move_to(ctx.author.voice.channel)

    # Play random if no query provided
    if not query:
        await play_random_song(ctx)
        return

    # Add to queue
    audio_info = await get_audio_info(query, is_requested=True)
    if audio_info:
        await song_queue.put(audio_info)
        if not ctx.voice_client.is_playing():
            await play_next(ctx)
        else:
            await ctx.send(f"➕ Added to queue: **{audio_info['title']}**")
    else:
        await ctx.send("⚠️ Couldn't find that song!")

@bot.command()
async def skip(ctx):
    """Skip the current song"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped current song")
    else:
        await ctx.send("No song is currently playing!")

@bot.command()
async def stop(ctx):
    """Stop the bot and clear the queue"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queue = asyncio.Queue()  # Reset queue
        await ctx.send("⏹️ Stopped playback and cleared queue")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def current(ctx):
    """Show the currently playing track"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.send(f"🔊 Currently playing track {current_track_number}")
    else:
        await ctx.send("No song is currently playing!")

@bot.command()
async def queue(ctx):
    """Show the current queue"""
    if song_queue.empty():
        return await ctx.send("The queue is empty! I'll play a random song next.")
    
    # Note: This is a simple implementation. For a full queue list, you'd need to track songs differently
    await ctx.send("There are songs in the queue. Currently playing the next one.")

@bot.command()
async def addsong(ctx, url: str, title: str, artist: str):
    """Add a song to the predefined list (admin only)"""
    # Add permission check if you want
    try:
        # Strip whitespace from inputs
        url = url.strip()
        title = title.strip()
        artist = artist.strip()
        
        with open('playlist.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([url, title, artist])
        await ctx.send(f"Added **{title}** by **{artist}** to the playlist!")
    except Exception as e:
        await ctx.send(f"⚠️ Error adding song: {e}")

@bot.command()
async def showplaylist(ctx):
    """Show all songs in the predefined playlist"""
    try:
        with open('playlist.csv', 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            playlist = [strip_whitespace(row) for row in reader if row]  # Read and clean all rows
            
        if not playlist:
            await ctx.send("The playlist is currently empty.")
            return
        
        playlist_text = "\n".join(
            f"{i+1}. {row[1] if len(row) > 1 else 'Unknown Track'} by "
            f"{row[2] if len(row) > 2 else 'Unknown Artist'}"
            for i, row in enumerate(playlist)
        )
        await ctx.send(f"🎵 Playlist (Total: {len(playlist)} songs):\n{playlist_text}")
    except FileNotFoundError:
        await ctx.send("The playlist file doesn't exist yet!")
    except Exception as e:
        await ctx.send(f"⚠️ Error loading playlist: {e}")

bot.run(YOUR_BOT_TOKEN_HERE)