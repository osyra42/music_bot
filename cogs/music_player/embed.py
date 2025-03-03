import disnake
from disnake.ext import commands
import logging

logger = logging.getLogger("disnake")

class EmbedManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_media_embed(self, title, description, color=disnake.Color.blurple()):
        """Create a visually appealing embed for the media player."""
        try:
            embed = disnake.Embed(title=title, description=description, color=color)

            # Read the content from signature.txt
            try:
                with open('signature.txt', 'r') as file:
                    signature_text = file.read().strip()
                embed.set_footer(text=signature_text)
            except FileNotFoundError:
                logger.warning("signature.txt not found, skipping footer.")
            except Exception as e:
                logger.error(f"Error reading signature.txt: {e}", exc_info=True)

            return embed
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return disnake.Embed(title="Error", description=f"An error occurred: {str(e)}",
                                 color=disnake.Color.red())

def setup(bot):
    bot.add_cog(EmbedManager(bot))
