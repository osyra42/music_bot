# cogs/radio/__init__.py
from .radio_mode import RadioMode
from .radio_controls import RadioControls

def setup(bot):
    bot.add_cog(RadioMode(bot))
    bot.add_cog(RadioControls(bot))
