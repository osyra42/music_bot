# cogs/radio/radio_controls.py
import disnake
from disnake.ext import commands
from disnake import ui
import logging
from .utils import RadioUtils

logger = logging.getLogger("disnake")

class RadioSettingsView(ui.View):
    """View for radio settings."""
    
    def __init__(self, cog, timeout=180):
        """Initialize the radio settings view.
        
        Args:
            cog: The RadioControls cog
            timeout (int): View timeout in seconds
        """
        super().__init__(timeout=timeout)
        self.cog = cog
        self.config = RadioUtils.load_config()
    
    @ui.button(label="Toggle TTS", style=disnake.ButtonStyle.primary)
    async def toggle_tts_button(self, button: ui.Button, inter: disnake.Interaction):
        """Toggle TTS on/off."""
        self.config["tts_enabled"] = not self.config.get("tts_enabled", True)
        RadioUtils.save_config(self.config)
        
        status = "enabled" if self.config["tts_enabled"] else "disabled"
        await inter.response.send_message(f"TTS announcements {status}.", ephemeral=True)
    
    @ui.button(label="Toggle News", style=disnake.ButtonStyle.primary)
    async def toggle_news_button(self, button: ui.Button, inter: disnake.Interaction):
        """Toggle news updates on/off."""
        self.config["news_enabled"] = not self.config.get("news_enabled", True)
        RadioUtils.save_config(self.config)
        
        status = "enabled" if self.config["news_enabled"] else "disabled"
        await inter.response.send_message(f"News updates {status}.", ephemeral=True)
    
    @ui.button(label="Toggle Trivia", style=disnake.ButtonStyle.primary)
    async def toggle_trivia_button(self, button: ui.Button, inter: disnake.Interaction):
        """Toggle song trivia on/off."""
        self.config["trivia_enabled"] = not self.config.get("trivia_enabled", True)
        RadioUtils.save_config(self.config)
        
        status = "enabled" if self.config["trivia_enabled"] else "disabled"
        await inter.response.send_message(f"Song trivia {status}.", ephemeral=True)
    
    @ui.button(label="Change Host Style", style=disnake.ButtonStyle.secondary)
    async def host_style_button(self, button: ui.Button, inter: disnake.Interaction):
        """Change the host personality style."""
        # Create a select menu for host personality
        await inter.response.send_modal(
            title="Host Personality",
            custom_id="host_personality_modal",
            components=[
                ui.TextInput(
                    label="Select Personality",
                    custom_id="personality",
                    placeholder="friendly, formal, humorous, energetic",
                    value=self.config.get("host_personality", "friendly"),
                    style=disnake.TextInputStyle.short,
                    required=True
                )
            ]
        )
    
    @ui.button(label="News Frequency", style=disnake.ButtonStyle.secondary)
    async def news_frequency_button(self, button: ui.Button, inter: disnake.Interaction):
        """Change the news update frequency."""
        await inter.response.send_modal(
            title="News Frequency",
            custom_id="news_frequency_modal",
            components=[
                ui.TextInput(
                    label="Songs Between News (3-10)",
                    custom_id="frequency",
                    placeholder="Enter a number between 3 and 10",
                    value=str(self.config.get("news_frequency", 5)),
                    style=disnake.TextInputStyle.short,
                    required=True
                )
            ]
        )

class RadioControls(commands.Cog):
    """Radio controls cog for managing radio mode."""
    
    def __init__(self, bot):
        """Initialize the radio controls cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.config = RadioUtils.load_config()
        logger.info("Radio Controls cog initialized")
    
    @commands.slash_command(name="radio_settings", description="Configure radio mode settings")
    @commands.has_permissions(manage_guild=True)
    async def radio_settings(self, inter: disnake.ApplicationCommandInteraction):
        """Configure radio mode settings."""
        view = RadioSettingsView(self)
        
        embed = disnake.Embed(
            title="Radio Mode Settings",
            description="Configure your radio experience",
            color=disnake.Color.blurple()
        )
        
        # Add current settings to the embed
        embed.add_field(
            name="Current Settings",
            value=(
                f"**TTS Announcements:** {'Enabled' if self.config.get('tts_enabled', True) else 'Disabled'}\n"
                f"**News Updates:** {'Enabled' if self.config.get('news_enabled', True) else 'Disabled'}\n"
                f"**Song Trivia:** {'Enabled' if self.config.get('trivia_enabled', True) else 'Disabled'}\n"
                f"**Host Personality:** {self.config.get('host_personality', 'friendly').capitalize()}\n"
                f"**News Frequency:** Every {self.config.get('news_frequency', 5)} songs\n"
                f"**Dynamic Content:** {'Enabled' if self.config.get('time_based_content', True) else 'Disabled'}"
            ),
            inline=False
        )
        
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        """Handle modal submissions for radio settings."""
        if inter.custom_id == "host_personality_modal":
            personality = inter.text_values["personality"].lower()
            valid_personalities = ["friendly", "formal", "humorous", "energetic"]
            
            if personality not in valid_personalities:
                await inter.response.send_message(
                    f"Invalid personality. Please choose from: {', '.join(valid_personalities)}",
                    ephemeral=True
                )
                return
            
            self.config["host_personality"] = personality
            RadioUtils.save_config(self.config)
            
            await inter.response.send_message(
                f"Host personality set to: {personality.capitalize()}",
                ephemeral=True
            )
        
        elif inter.custom_id == "news_frequency_modal":
            try:
                frequency = int(inter.text_values["frequency"])
                
                if not (3 <= frequency <= 10):
                    await inter.response.send_message(
                        "Frequency must be between 3 and 10 songs.",
                        ephemeral=True
                    )
                    return
                
                self.config["news_frequency"] = frequency
                RadioUtils.save_config(self.config)
                
                await inter.response.send_message(
                    f"News frequency set to: Every {frequency} songs",
                    ephemeral=True
                )
            except ValueError:
                await inter.response.send_message(
                    "Please enter a valid number.",
                    ephemeral=True
                )

def setup(bot):
    bot.add_cog(RadioControls(bot))
