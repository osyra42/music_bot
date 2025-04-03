# cogs/radio/tts_engine.py
import os
import logging
import asyncio
import hashlib
import tempfile
import disnake
from config import TTS_PROVIDER, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

# Import the appropriate TTS library based on the provider
if TTS_PROVIDER == "gtts":
    from gtts import gTTS
elif TTS_PROVIDER == "aws":
    import boto3

logger = logging.getLogger("disnake")

class TTSEngine:
    """Text-to-Speech engine for radio mode announcements."""

    def __init__(self, cache_dir="tts_cache"):
        """Initialize the TTS engine.

        Args:
            cache_dir (str): Directory to cache TTS audio files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"TTS Engine initialized with cache directory: {cache_dir}")

    def _get_cache_path(self, text, lang="en"):
        """Generate a cache path for the given text and language.

        Args:
            text (str): Text to convert to speech
            lang (str): Language code

        Returns:
            str: Path to the cached audio file
        """
        # Create a hash of the text and language to use as the filename
        text_hash = hashlib.md5(f"{text}_{lang}".encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{text_hash}.mp3")

    async def text_to_speech(self, text, lang="en", slow=False):
        """Convert text to speech and return the path to the audio file.

        Args:
            text (str): Text to convert to speech
            lang (str): Language code
            slow (bool): Whether to speak slowly

        Returns:
            str: Path to the audio file
        """
        cache_path = self._get_cache_path(text, lang)

        # Check if the audio is already cached
        if os.path.exists(cache_path):
            logger.info(f"Using cached TTS audio: {cache_path}")
            return cache_path

        # Generate the audio file
        try:
            logger.info(f"Generating TTS audio for: {text[:50]}...")

            # Run the TTS generation in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()

            if TTS_PROVIDER == "gtts":
                # Use Google TTS
                await loop.run_in_executor(
                    None,
                    lambda: gTTS(text=text, lang=lang, slow=slow).save(cache_path)
                )
            elif TTS_PROVIDER == "aws":
                # Use AWS Polly
                if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION]):
                    logger.error("AWS credentials not configured. Falling back to Google TTS.")
                    await loop.run_in_executor(
                        None,
                        lambda: gTTS(text=text, lang=lang, slow=slow).save(cache_path)
                    )
                else:
                    # Create a Polly client
                    polly = boto3.Session(
                        aws_access_key_id=AWS_ACCESS_KEY,
                        aws_secret_access_key=AWS_SECRET_KEY,
                        region_name=AWS_REGION
                    ).client('polly')

                    # Request speech synthesis
                    response = await loop.run_in_executor(
                        None,
                        lambda: polly.synthesize_speech(
                            Text=text,
                            OutputFormat='mp3',
                            VoiceId='Joanna'  # Female voice
                        )
                    )

                    # Save the audio stream to a file
                    if "AudioStream" in response:
                        await loop.run_in_executor(
                            None,
                            lambda: response["AudioStream"].read().save(cache_path)
                        )
            else:
                # Default to Google TTS if provider is not recognized
                logger.warning(f"Unknown TTS provider: {TTS_PROVIDER}. Using Google TTS.")
                await loop.run_in_executor(
                    None,
                    lambda: gTTS(text=text, lang=lang, slow=slow).save(cache_path)
                )

            logger.info(f"TTS audio generated and saved to: {cache_path}")
            return cache_path
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}", exc_info=True)
            return None

    async def create_song_intro(self, song_title, artist, trivia=None):
        """Create a song introduction.

        Args:
            song_title (str): Title of the song
            artist (str): Artist of the song
            trivia (str, optional): Trivia about the song or artist

        Returns:
            str: Path to the audio file
        """
        intro_text = f"Now playing {song_title} by {artist}."

        if trivia:
            intro_text += f" {trivia}"

        return await self.text_to_speech(intro_text)

    async def create_news_announcement(self, news_items, category="general"):
        """Create a news announcement.

        Args:
            news_items (list): List of news items (dict with 'title' and 'description')
            category (str): News category

        Returns:
            str: Path to the audio file
        """
        if not news_items:
            return None

        news_text = f"Here are the latest {category} news updates. "

        for i, item in enumerate(news_items[:3]):  # Limit to 3 news items
            news_text += f"{item['title']}. {item['description']} "

        news_text += "That's all for now. Back to the music."

        return await self.text_to_speech(news_text)

    def cleanup_cache(self, max_age_days=7):
        """Clean up old cached TTS files.

        Args:
            max_age_days (int): Maximum age of cache files in days
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Removed old TTS cache file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up TTS cache: {e}", exc_info=True)
