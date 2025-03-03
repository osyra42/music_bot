import disnake
from disnake.ext import commands
import logging
import sqlite3

logger = logging.getLogger("disnake")

class StatsVoting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_connection = sqlite3.connect('music_bot.db')
        self.db_cursor = self.db_connection.cursor()

        # Create tables if they don't exist
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS song_stats (
                title TEXT PRIMARY KEY,
                played INTEGER DEFAULT 0,
                requested INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                last_played TIMESTAMP
            )
        """)
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                message_id INTEGER,
                user_id INTEGER,
                emoji TEXT,
                PRIMARY KEY (message_id, user_id, emoji)
            )
        """)
        self.db_connection.commit()

    def update_song_stats(self, title: str, requested: bool = False, skipped: bool = False):
        """Update the song stats."""
        self.db_cursor.execute("""
            INSERT OR REPLACE INTO song_stats (title, played, requested, skipped, last_played)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            1 if requested else 0,
            1 if skipped else 0,
            disnake.utils.utcnow().isoformat()
        ))
        self.db_connection.commit()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.User):
        """
        Handles reaction add events for emoji voting.
        """
        if user.bot:
            return

        emoji = str(reaction.emoji)
        if emoji not in ["👍", "👎", "⚠️"]:
            return

        # Store vote data in the database
        try:
            self.db_cursor.execute("""
                INSERT OR IGNORE INTO votes (message_id, user_id, emoji)
                VALUES (?, ?, ?)
            """, (reaction.message.id, user.id, emoji))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

        # Log reports for review by server admins
        if emoji == "⚠️":
            logger.info(f"Reported song: {reaction.message.embeds[0].title} by {user.name}")

    def get_song_stats(self, title: str):
        """Retrieve the song stats."""
        self.db_cursor.execute("""
            SELECT played, requested, skipped, last_played FROM song_stats WHERE title = ?
        """, (title,))
        return self.db_cursor.fetchone()

def setup(bot):
    bot.add_cog(StatsVoting(bot))

    def update_song_stats(self, title: str, requested: bool = False, skipped: bool = False):
        """Update the song stats."""
        self.db_cursor.execute("""
            INSERT OR REPLACE INTO song_stats (title, played, requested, skipped, last_played)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            1 if requested else 0,
            1 if skipped else 0,
            disnake.utils.utcnow().isoformat()
        ))
        self.db_connection.commit()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.User):
        """
        Handles reaction add events for emoji voting.
        """
        if user.bot:
            return

        emoji = str(reaction.emoji)
        if emoji not in ["👍", "👎", "⚠️"]:
            return

        # Store vote data in the database
        try:
            self.db_cursor.execute("""
                INSERT OR IGNORE INTO votes (message_id, user_id, emoji)
                VALUES (?, ?, ?)
            """, (reaction.message.id, user.id, emoji))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)

        # Log reports for review by server admins
        if emoji == "⚠️":
            logger.info(f"Reported song: {reaction.message.embeds[0].title} by {user.name}")

def setup(bot):
    bot.add_cog(StatsVoting(bot))
