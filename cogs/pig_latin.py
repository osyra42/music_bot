# cogs/pig_latin.py
import disnake
from disnake.ext import commands

class PigLatinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="to_pig_latin", description="Convert text to Pig Latin.")
    async def to_pig_latin(self, inter: disnake.ApplicationCommandInteraction, text: str):
        """Convert text to Pig Latin."""
        pig_latin_text = self.convert_to_pig_latin(text)
        embed = disnake.Embed(title="Pig Latin Conversion", description=f"Original: {text}\nPig Latin: {pig_latin_text}", color=0x00ff00)
        await inter.response.send_message(embed=embed)

    def convert_to_pig_latin(self, text: str) -> str:
        """Convert a given text to Pig Latin."""
        vowels = "aeiouAEIOU"
        words = text.split()
        pig_latin_words = []

        for word in words:
            if word[0] in vowels:
                pig_latin_word = word + "way"
            else:
                for i, char in enumerate(word):
                    if char in vowels:
                        pig_latin_word = word[i:] + word[:i] + "ay"
                        break
            pig_latin_words.append(pig_latin_word)

        return " ".join(pig_latin_words)

def setup(bot):
    bot.add_cog(PigLatinCog(bot))
