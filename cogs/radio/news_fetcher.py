# cogs/radio/news_fetcher.py
import logging
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from config import NEWS_API_KEY

logger = logging.getLogger("disnake")

class NewsFetcher:
    """News fetcher for radio mode."""

    def __init__(self, api_key=NEWS_API_KEY, cache_dir="news_cache"):
        """Initialize the news fetcher.

        Args:
            api_key (str, optional): NewsAPI API key
            cache_dir (str): Directory to cache news data
        """
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "news_cache.json")
        self.cache_expiry = 30 * 60  # 30 minutes in seconds

        os.makedirs(cache_dir, exist_ok=True)
        logger.info(f"News Fetcher initialized with cache directory: {cache_dir}")

    async def _fetch_from_newsapi(self, category="technology", country="us", page_size=5):
        """Fetch news from NewsAPI.

        Args:
            category (str): News category
            country (str): Country code
            page_size (int): Number of news items to fetch

        Returns:
            list: List of news items
        """
        if not self.api_key:
            logger.warning("NewsAPI key not provided. Using fallback news.")
            return self._get_fallback_news(category)

        url = f"https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": self.api_key,
            "category": category,
            "country": country,
            "pageSize": page_size
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "ok":
                            return data.get("articles", [])
                        else:
                            logger.error(f"NewsAPI error: {data.get('message')}")
                    else:
                        logger.error(f"NewsAPI HTTP error: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching news from NewsAPI: {e}", exc_info=True)

        return self._get_fallback_news(category)

    def _get_fallback_news(self, category="technology"):
        """Get fallback news when API is unavailable.

        Args:
            category (str): News category

        Returns:
            list: List of fallback news items
        """
        fallback_news = {
            "technology": [
                {
                    "title": "New AI breakthrough helps solve complex problems",
                    "description": "Researchers have developed a new AI model that can solve complex problems in record time."
                },
                {
                    "title": "Tech companies announce new privacy features",
                    "description": "Major tech companies are rolling out new privacy features to protect user data."
                }
            ],
            "general": [
                {
                    "title": "Global cooperation leads to major environmental agreement",
                    "description": "Countries around the world have agreed to reduce carbon emissions by 30% over the next decade."
                },
                {
                    "title": "New educational initiative launched worldwide",
                    "description": "A new program aims to improve access to education in underserved communities."
                }
            ],
            "weather": [
                {
                    "title": "Weather forecast for the week ahead",
                    "description": "Expect mild temperatures and partly cloudy skies for most of the week."
                },
                {
                    "title": "Climate scientists report on seasonal trends",
                    "description": "This season is showing typical patterns with some regional variations."
                }
            ]
        }

        return fallback_news.get(category, fallback_news["general"])

    async def _fetch_from_rss(self, feed_url):
        """Fetch news from an RSS feed.

        Args:
            feed_url (str): URL of the RSS feed

        Returns:
            list: List of news items
        """
        try:
            import feedparser

            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)

                        news_items = []
                        for entry in feed.entries[:5]:  # Limit to 5 items
                            news_items.append({
                                "title": entry.title,
                                "description": entry.get("summary", "").split(".")[0] + "."  # First sentence only
                            })

                        return news_items
        except Exception as e:
            logger.error(f"Error fetching news from RSS: {e}", exc_info=True)

        return []

    def _load_cache(self):
        """Load cached news data.

        Returns:
            dict: Cached news data
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    cache = json.load(f)

                # Check if cache is expired
                if "timestamp" in cache:
                    cache_time = datetime.fromisoformat(cache["timestamp"])
                    if (datetime.now() - cache_time).total_seconds() < self.cache_expiry:
                        return cache
            except Exception as e:
                logger.error(f"Error loading news cache: {e}", exc_info=True)

        return None

    def _save_cache(self, data):
        """Save news data to cache.

        Args:
            data (dict): News data to cache
        """
        try:
            data["timestamp"] = datetime.now().isoformat()

            with open(self.cache_file, "w") as f:
                json.dump(data, f)

            logger.info(f"News cache saved to: {self.cache_file}")
        except Exception as e:
            logger.error(f"Error saving news cache: {e}", exc_info=True)

    async def get_news(self, category="technology", force_refresh=False):
        """Get news items for the specified category.

        Args:
            category (str): News category
            force_refresh (bool): Whether to force a refresh of the cache

        Returns:
            list: List of news items
        """
        # Check cache first
        if not force_refresh:
            cache = self._load_cache()
            if cache and category in cache:
                logger.info(f"Using cached news for category: {category}")
                return cache[category]

        # Fetch fresh news
        news_items = await self._fetch_from_newsapi(category)

        # Update cache
        cache = self._load_cache() or {}
        cache[category] = news_items
        self._save_cache(cache)

        return news_items

    async def get_weather(self):
        """Get weather information.

        Returns:
            list: List of weather items
        """
        # This could be expanded to use a real weather API
        return await self.get_news(category="weather")

    def cleanup_cache(self):
        """Clean up old cached news data."""
        if os.path.exists(self.cache_file):
            try:
                cache = self._load_cache()
                if cache and "timestamp" in cache:
                    cache_time = datetime.fromisoformat(cache["timestamp"])
                    if (datetime.now() - cache_time).total_seconds() > 24 * 60 * 60:  # 24 hours
                        os.remove(self.cache_file)
                        logger.info(f"Removed old news cache file: {self.cache_file}")
            except Exception as e:
                logger.error(f"Error cleaning up news cache: {e}", exc_info=True)
