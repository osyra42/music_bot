import os
import glob
from disnake.ext import commands

def setup(bot):
    cogs = []
    for path in glob.glob("cogs/**/*.py", recursive=True):
        cogs.append(path.replace("/", ".")[:-3])

    for cog in cogs:
        try:
            bot.load_extension(cog)
            print(f"Loaded {cog} cog")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")
