# utils/cog_manager.py
import os
import logging

logger = logging.getLogger("disnake")

def load_cogs(bot):
    """Load all cogs from the 'cogs' directory and its subdirectories."""
    cogs_dir = "cogs"
    for root, dirs, files in os.walk(cogs_dir):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_"):  # Ignore __init__.py and private files
                try:
                    # Construct the module path
                    module_path = os.path.relpath(root, start=cogs_dir).replace(os.sep, ".")
                    if module_path == ".":
                        module_path = ""
                    else:
                        module_path += "."
                    cog_name = f"{cogs_dir}.{module_path}{filename[:-3]}"  # Remove .py extension
                    bot.load_extension(cog_name)
                    logger.info(f"Successfully loaded cog: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_name}: {e}")
