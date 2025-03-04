# cogs/music/__init__.py
from .player import MusicPlayer
from .controls import MusicControls

def setup(bot):
    bot.add_cog(MusicPlayer(bot))
    bot.add_cog(MusicControls(bot, queue=None, last_played=None))
