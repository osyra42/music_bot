import os
import disnake
from disnake.ext import commands
import yt_dlp as youtube_dl
import asyncio
import secret  # Import your secret.py file

# Suppress noise about console usage from yt-dlp
youtube_dl.utils.bug_reports_message = lambda: ''

# Options for yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
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

# Music cog
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("🎵 Music cog loaded!")

    async def send_embed(self, ctx, description, color=disnake.Color.green()):
        """Helper function to send an embed."""
        embed = disnake.Embed(description=description, color=color)
        await ctx.send(embed=embed)

    @commands.slash_command(description="Join a voice channel", guild_ids=[secret.TEST_GUILD_ID])
    async def join(self, ctx):
        if not ctx.author.voice:
            await self.send_embed(ctx, "🚫 You are not in a voice channel!", disnake.Color.red())
            print(f"🚫 {ctx.author} tried to use /join but is not in a voice channel.")
            return

        if ctx.guild.voice_client:
            await self.send_embed(ctx, "🚫 I'm already in a voice channel!", disnake.Color.red())
            print(f"🚫 {ctx.author} tried to use /join but the bot is already in a voice channel.")
            return

        await ctx.response.defer()  # Defer the response
        channel = ctx.author.voice.channel
        await channel.connect()
        await self.send_embed(ctx, f"🎤 Joined {channel.name}!")
        print(f"🎤 Joined voice channel: {channel.name}")

    @commands.slash_command(description="Leave the voice channel", guild_ids=[secret.TEST_GUILD_ID])
    async def leave(self, ctx):
        if ctx.guild.voice_client:
            await ctx.response.defer()  # Defer the response
            await ctx.guild.voice_client.disconnect()
            await self.send_embed(ctx, "👋 Left the voice channel!")
            print(f"👋 Left voice channel in {ctx.guild.name}")
        else:
            await self.send_embed(ctx, "🚫 I'm not in a voice channel!", disnake.Color.red())
            print(f"🚫 {ctx.author} tried to use /leave but the bot is not in a voice channel.")

    @commands.slash_command(description="Play audio from a YouTube URL", guild_ids=[secret.TEST_GUILD_ID])
    async def play(self, ctx, url: str):
        if not ctx.guild.voice_client:
            await self.send_embed(ctx, "🚫 I'm not in a voice channel!", disnake.Color.red())
            print(f"🚫 {ctx.author} tried to use /play but the bot is not in a voice channel.")
            return

        # Defer the response to indicate the bot is processing the request
        await ctx.response.defer()

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.guild.voice_client.play(player, after=lambda e: print(f'🚨 Player error: {e}') if e else None)

            await self.send_embed(ctx, f"🎶 Now playing: **{player.title}**")
            print(f"🎶 Now playing: {player.title} (URL: {url})")
        except Exception as e:
            await self.send_embed(ctx, f"🚨 An error occurred: {e}", disnake.Color.red())
            print(f"🚨 Error playing audio: {e}")

    @commands.slash_command(description="Stop playing audio", guild_ids=[secret.TEST_GUILD_ID])
    async def stop(self, ctx):
        if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
            await ctx.response.defer()  # Defer the response
            ctx.guild.voice_client.stop()
            await self.send_embed(ctx, "⏹️ Stopped playing audio!")
            print(f"⏹️ Stopped playing audio in {ctx.guild.name}")
        else:
            await self.send_embed(ctx, "🚫 I'm not playing anything!", disnake.Color.red())
            print(f"🚫 {ctx.author} tried to use /stop but the bot is not playing anything.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user and after.channel is None:
            voice_client = disnake.utils.get(self.bot.voice_clients, guild=member.guild)
            if voice_client:
                await voice_client.disconnect()
                print(f"👋 Disconnected from voice channel in {member.guild.name} due to leaving.")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(Music(bot))