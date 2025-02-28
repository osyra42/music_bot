import disnake
from disnake.ext import commands
import logging
import asyncio

logger = logging.getLogger("disnake")

class Disconnect(commands.Cog):
    """A cog for handling bot disconnection from voice channels."""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="disconnect", description="Disconnect the bot from the voice channel.")
    async def disconnect(self, inter: disnake.ApplicationCommandInteraction):
        """
        Disconnects the bot from the voice channel.

        Args:
            inter (disnake.ApplicationCommandInteraction): The interaction that triggered the command.
        """
        try:
            if inter.guild.voice_client is None:
                await inter.response.send_message("I'm not connected to a voice channel.", ephemeral=True)
                return

            logger.info("Disconnecting from voice channel.")
            await inter.guild.voice_client.disconnect()
            embed = disnake.Embed(title="Disconnected", description="The bot has been disconnected from the voice channel.", color=0x00ff00)
            await inter.response.send_message(embed=embed)
        except Exception as e:
            logger.exception("Error occurred during disconnect command.")
            await inter.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Disconnects the bot if it is alone in the voice channel after a 30-second delay.

        Args:
            member (disnake.Member): The member whose voice state changed.
            before (disnake.VoiceState): The voice state before the change.
            after (disnake.VoiceState): The voice state after the change.
        """
        try:
            if member == self.bot.user:
                return

            voice_client = member.guild.voice_client
            if voice_client and voice_client.channel:
                if len(voice_client.channel.members) == 1 and voice_client.channel.members[0] == self.bot.user:
                    logger.info("Bot is alone in the voice channel. Waiting 30 seconds before disconnecting...")
                    await asyncio.sleep(30)

                    if len(voice_client.channel.members) == 1 and voice_client.channel.members[0] == self.bot.user:
                        logger.info("Still alone after 30 seconds. Disconnecting...")
                        await voice_client.disconnect()
        except Exception as e:
            logger.exception("Error occurred during voice state update.")

def setup(bot):
    bot.add_cog(Disconnect(bot))
