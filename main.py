import disnake
from disnake.ext import commands
import yt_dlp as youtube_dl
import asyncio
import secret

# Suppress noise about console usage from yt-dlp
youtube_dl.utils.bug_reports_message = lambda: ''

# Options for yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # Bind to IPv4 since IPv6 addresses cause issues sometimes
}

# FFmpeg options for audio streaming
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Bot setup
intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper class to handle YouTube audio
class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)  # Pass source and volume to the parent class
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(disnake.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Command to join a voice channel
@bot.slash_command(description="Join a voice channel", guild_ids=[secret.TEST_GUILD_ID])
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel!")
        return

    if ctx.guild.voice_client:
        await ctx.send("I'm already in a voice channel!")
        return

    await ctx.response.defer()  # Defer the response
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f"Joined {channel.name}!")

# Command to leave a voice channel
@bot.slash_command(description="Leave the voice channel", guild_ids=[secret.TEST_GUILD_ID])
async def leave(ctx):
    if ctx.guild.voice_client:
        await ctx.response.defer()  # Defer the response
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel!")
    else:
        await ctx.send("I'm not in a voice channel!")

# Command to play audio from a YouTube URL
@bot.slash_command(description="Play audio from a YouTube URL", guild_ids=[secret.TEST_GUILD_ID])
async def play(ctx, url: str):
    if not ctx.guild.voice_client:
        await ctx.send("I'm not in a voice channel!")
        return

    # Defer the response to indicate the bot is processing the request
    await ctx.response.defer()

    try:
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.guild.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f"Now playing: {player.title}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Command to stop playing audio
@bot.slash_command(description="Stop playing audio", guild_ids=[secret.TEST_GUILD_ID])
async def stop(ctx):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        await ctx.response.defer()  # Defer the response
        ctx.guild.voice_client.stop()
        await ctx.send("Stopped playing audio!")
    else:
        await ctx.send("I'm not playing anything!")

# Ensure the bot leaves the voice channel when it's done
@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel is None:
        voice_client = disnake.utils.get(bot.voice_clients, guild=member.guild)
        if voice_client:
            await voice_client.disconnect()

# Sync commands when the bot starts
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Commands are ready to be used!")

# Run the bot
if __name__ == "__main__":
    bot.run(secret.YOUR_BOT_TOKEN)