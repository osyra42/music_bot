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

# Store queues per server
song_queues = {}

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

# Load playlist from CSV
def load_playlist():
    playlist = []
    try:
        with open('playlist.csv', 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:  # Skip empty rows
                    playlist.append(row[0])  # First column contains URLs
        return playlist
    except FileNotFoundError:
        print("Warning: playlist.csv not found. Using empty playlist.")
        return []

# Initialize playlist
playlist = load_playlist()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def get_audio_info(query):
    """Extract audio information from YouTube"""
    with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:  # Handle playlists/search results
                info = info['entries'][0]
            return {
                'url': info['url'],
                'title': info.get('title', 'Unknown Track')
            }
        except Exception as e:
            print(f"Error getting audio info: {e}")
            return None

async def play_random_song(ctx):
    """Play a random song from playlist"""
    if ctx.guild.id not in song_queues:
        song_queues[ctx.guild.id] = asyncio.Queue()
    
    if not playlist:
        await ctx.send("⚠️ The playlist is empty! Add some songs first.")
        return
    
    random_song = random.choice(playlist)
    await song_queues[ctx.guild.id].put(random_song)
    await play_next(ctx)

async def play_next(ctx):
    """Play the next song in queue"""
    if not ctx.voice_client:
        return

    # Initialize queue if needed
    if ctx.guild.id not in song_queues:
        song_queues[ctx.guild.id] = asyncio.Queue()

    # Play random song if queue is empty
    if song_queues[ctx.guild.id].empty():
        await play_random_song(ctx)
        return

    song = await song_queues[ctx.guild.id].get()
    audio_info = await get_audio_info(song)

    if not audio_info:
        await ctx.send("⚠️ Couldn't process this song. Trying another...")
        await play_next(ctx)
        return

    try:
        def after_playing(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)

        source = discord.FFmpegPCMAudio(audio_info['url'], **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=after_playing)
        await ctx.send(f"🎵 Now playing: **{audio_info['title']}**")
    except Exception as e:
        print(f"Error starting playback: {e}")
        await ctx.send("⚠️ Error playing song. Skipping...")
        await play_next(ctx)

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

    # Initialize queue if needed
    if ctx.guild.id not in song_queues:
        song_queues[ctx.guild.id] = asyncio.Queue()

    # Play random if no query provided
    if not query:
        await play_random_song(ctx)
        return

    # Add to queue
    await song_queues[ctx.guild.id].put(query)
    if not ctx.voice_client.is_playing():
        await play_next(ctx)
    else:
        await ctx.send(f"➕ Added to queue: **{query}**")

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
        if ctx.guild.id in song_queues:
            song_queues[ctx.guild.id] = asyncio.Queue()  # Reset queue
        await ctx.send("⏹️ Stopped playback and cleared queue")
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def queue(ctx):
    """Show the current queue"""
    if ctx.guild.id not in song_queues or song_queues[ctx.guild.id].empty():
        return await ctx.send("The queue is empty! I'll play a random song next.")
    
    # Note: This is a simple implementation. For a full queue list, you'd need to track songs differently
    await ctx.send("There are songs in the queue. Currently playing the next one.")

@bot.command()
async def addsong(ctx, *, song):
    """Add a song to the predefined list (admin only)"""
    # Add permission check if you want
    playlist.append(song)
    # Save to CSV
    with open('playlist.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([song])
    await ctx.send(f"Added **{song}** to the playlist!")

@bot.command()
async def showplaylist(ctx):
    """Show all songs in the predefined playlist"""
    if not playlist:
        await ctx.send("The playlist is currently empty.")
        return
    
    playlist_text = "\n".join(f"{i+1}. {song}" for i, song in enumerate(playlist))
    await ctx.send(f"🎵 Playlist (Total: {len(playlist)} songs):\n{playlist_text}")

bot.run(YOUR_BOT_TOKEN_HERE)