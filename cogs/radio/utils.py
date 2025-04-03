# cogs/radio/utils.py
import logging
import json
import os
import random
from datetime import datetime

logger = logging.getLogger("disnake")

class RadioUtils:
    """Utility functions for radio mode."""
    
    @staticmethod
    def load_config(config_file="radio_config.json"):
        """Load radio configuration from file.
        
        Args:
            config_file (str): Path to the configuration file
            
        Returns:
            dict: Radio configuration
        """
        default_config = {
            "tts_enabled": True,
            "news_enabled": True,
            "news_frequency": 5,  # After every 5 songs
            "news_categories": ["technology", "general"],
            "host_personality": "friendly",
            "trivia_enabled": True,
            "time_based_content": True,
            "morning_greeting": "Good morning! It's a brand new day with your favorite music.",
            "afternoon_greeting": "Good afternoon! Hope you're having a great day.",
            "evening_greeting": "Good evening! Time to relax with some great tunes.",
            "night_greeting": "It's night time. Enjoy some smooth tracks as you wind down."
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                
                # Merge with default config to ensure all keys exist
                merged_config = default_config.copy()
                merged_config.update(config)
                
                return merged_config
            except Exception as e:
                logger.error(f"Error loading radio config: {e}", exc_info=True)
        
        # If file doesn't exist or there's an error, create it with default values
        try:
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=4)
            
            logger.info(f"Created default radio config: {config_file}")
        except Exception as e:
            logger.error(f"Error creating radio config: {e}", exc_info=True)
        
        return default_config
    
    @staticmethod
    def save_config(config, config_file="radio_config.json"):
        """Save radio configuration to file.
        
        Args:
            config (dict): Radio configuration
            config_file (str): Path to the configuration file
            
        Returns:
            bool: Whether the save was successful
        """
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
            
            logger.info(f"Radio config saved to: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving radio config: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_time_of_day_greeting(config):
        """Get a greeting based on the time of day.
        
        Args:
            config (dict): Radio configuration
            
        Returns:
            str: Time-appropriate greeting
        """
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return config.get("morning_greeting", "Good morning!")
        elif 12 <= hour < 17:
            return config.get("afternoon_greeting", "Good afternoon!")
        elif 17 <= hour < 22:
            return config.get("evening_greeting", "Good evening!")
        else:
            return config.get("night_greeting", "Good night!")
    
    @staticmethod
    def get_song_trivia(song_title, artist):
        """Get trivia about a song or artist.
        
        Args:
            song_title (str): Title of the song
            artist (str): Artist of the song
            
        Returns:
            str: Trivia about the song or artist
        """
        # This could be expanded to use a real music information API
        generic_trivia = [
            f"Did you know that {artist} has been making music for over a decade?",
            f"This track by {artist} is one of their most popular songs.",
            f"{song_title} was released as part of an album that received critical acclaim.",
            f"{artist} wrote this song during a particularly creative period.",
            f"Fans often cite {song_title} as one of {artist}'s defining works.",
            f"The rhythm in {song_title} showcases {artist}'s unique musical style.",
            f"{artist} has cited this song as one of their personal favorites.",
            f"The lyrics in {song_title} were inspired by {artist}'s personal experiences.",
            f"This track features {artist}'s signature sound that fans have come to love.",
            f"{song_title} demonstrates why {artist} is considered a standout in their genre."
        ]
        
        return random.choice(generic_trivia)
    
    @staticmethod
    def should_play_news(songs_played, config):
        """Determine if news should be played.
        
        Args:
            songs_played (int): Number of songs played since last news
            config (dict): Radio configuration
            
        Returns:
            bool: Whether news should be played
        """
        if not config.get("news_enabled", True):
            return False
        
        news_frequency = config.get("news_frequency", 5)
        return songs_played >= news_frequency
    
    @staticmethod
    def get_dynamic_content_frequency(config):
        """Get dynamic content frequency based on time of day.
        
        Args:
            config (dict): Radio configuration
            
        Returns:
            int: Frequency for dynamic content
        """
        if not config.get("time_based_content", True):
            return config.get("news_frequency", 5)
        
        hour = datetime.now().hour
        
        # More frequent updates during peak hours, less frequent during night
        if 7 <= hour < 9 or 16 <= hour < 19:  # Morning and evening commute
            return 3  # More frequent updates
        elif 23 <= hour or hour < 5:  # Late night
            return 8  # Less frequent updates
        else:
            return 5  # Default frequency
    
    @staticmethod
    def format_song_info(song_data):
        """Format song information for display.
        
        Args:
            song_data (dict): Song data
            
        Returns:
            dict: Formatted song information
        """
        title = song_data.get("title", "Unknown Title")
        url = song_data.get("url", "")
        
        # Extract artist from title if possible
        if " - " in title:
            artist = title.split(" - ")[0].strip()
            song_title = title.split(" - ")[1].strip()
        else:
            artist = "Unknown Artist"
            song_title = title
        
        return {
            "title": song_title,
            "artist": artist,
            "full_title": title,
            "url": url
        }
