import disnake
from disnake.ext import commands
import logging
import asyncio

logger = logging.getLogger("disnake")

class Disconnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="disconnect", description="Disconnect the bot from the voice channel.")
    async def disconnect(self, inter: disnake.ApplicationCommandInteraction):
        """Disconnect the bot from the voice channel."""
        try:
            if inter.guild.voice_client is None:
                logger.error("I'm not connected to a voice channel.")
                await inter.response.send_message("I'm not connected to a voice channel.")
                return

            # Disconnect the bot
            logger.info("Disconnecting from voice channel.")
            await inter.guild.voice_client.disconnect()
            embed = disnake.Embed(title="Disconnected", description="The bot has been disconnected from the voice channel.", color=0x00ff00)
            await inter.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            await inter.response.send_message(f"An error occurred: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Disconnect the bot if it is alone in the voice channel after a 30-second delay."""
        try:
            if member == self.bot.user:
                return  # Ignore the bot's own voice state changes

            # Check if the bot is in a voice channel
            voice_client = member.guild.voice_client
            if voice_client and voice_client.channel:
                # Get the list of members in the voice channel excluding bots
                non_bot_members = [m for m in voice_client.channel.members if not m.bot]

                # If there are no non-bot members, start the 30-second timer
                if len(non_bot_members) == 0:
                    logger.info("No non-bot members in the voice channel. Waiting 30 seconds before disconnecting...")
                    await asyncio.sleep(30)  # Wait 30 seconds

                    # Recheck if there are still no non-bot members after the delay
                    non_bot_members = [m for m in voice_client.channel.members if not m.bot]
                    if len(non_bot_members) == 0:
                        logger.info("Still no non-bot members after 30 seconds. Disconnecting...")
                        await voice_client.disconnect()
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

def setup(bot):
    bot.add_cog(Disconnect(bot))