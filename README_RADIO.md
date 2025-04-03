# Radio Mode for Uta Yuki

This feature adds a radio-like experience to the Uta Yuki Discord bot, complete with TTS announcements, news updates, and dynamic content.

## Features

1. **TTS Voice Introductions**
   - Song introductions with title, artist, and trivia
   - News announcements with the latest updates
   - Time-of-day appropriate greetings

2. **News Updates**
   - Technology news
   - General news
   - Weather updates
   - Configurable frequency

3. **Dynamic Content**
   - Adjusts update frequency based on time of day
   - More frequent updates during peak hours
   - Less frequent updates during night hours

4. **Customization**
   - Admins can customize the host's personality (formal, humorous, etc.)
   - Configure news categories and frequency
   - Enable/disable TTS, news, and trivia

## Setup

1. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Get a NewsAPI key from [NewsAPI.org](https://newsapi.org/)
   - Add your API key to `config.py`

3. **TTS Configuration**
   - By default, Google TTS (gTTS) is used
   - For AWS Polly, set `TTS_PROVIDER = "aws"` in `config.py` and add your AWS credentials

## Usage

### Starting Radio Mode
Use the `/radio` command to start radio mode. The bot will join your voice channel and begin playing music with announcements.

### Stopping Radio Mode
Use the `/stop_radio` command to stop radio mode.

### Configuring Radio Settings
Use the `/radio_settings` command to configure radio mode settings:
- Toggle TTS announcements
- Toggle news updates
- Toggle song trivia
- Change host personality
- Adjust news frequency

## How It Works

1. **Playlist Management**
   - Songs are loaded from `playlist.txt`
   - The playlist is shuffled for variety

2. **TTS Announcements**
   - Generated using Google TTS or AWS Polly
   - Cached to reduce API calls and improve performance

3. **News Updates**
   - Fetched from NewsAPI or fallback sources
   - Cached for 30 minutes to reduce API calls

4. **Dynamic Content Scheduling**
   - Adjusts based on time of day
   - More frequent updates during morning and evening commute hours
   - Less frequent updates during night hours

## Customization

### Radio Configuration
Edit `radio_config.json` to customize the radio experience:
```json
{
    "tts_enabled": true,
    "news_enabled": true,
    "news_frequency": 5,
    "news_categories": ["technology", "general", "weather"],
    "host_personality": "friendly",
    "trivia_enabled": true,
    "time_based_content": true,
    "morning_greeting": "Good morning! It's a brand new day with your favorite music.",
    "afternoon_greeting": "Good afternoon! Hope you're having a great day.",
    "evening_greeting": "Good evening! Time to relax with some great tunes.",
    "night_greeting": "It's night time. Enjoy some smooth tracks as you wind down."
}
```

### Adding Custom Greetings
Edit the greetings in `radio_config.json` to customize the time-of-day greetings.

### Adding Custom Trivia
Extend the `get_song_trivia` method in `cogs/radio/utils.py` to add more song trivia or integrate with a music information API.

## Troubleshooting

### TTS Issues
- Make sure you have internet access for TTS API calls
- Check that the TTS cache directory (`tts_cache`) exists and is writable
- If using AWS Polly, verify your AWS credentials

### News API Issues
- Verify your NewsAPI key in `config.py`
- Check your NewsAPI usage limits
- The system will fall back to predefined news if the API is unavailable

### Playback Issues
- Ensure FFmpeg is installed on your system
- Check that the bot has permission to join and speak in voice channels
- Verify that the playlist file contains valid YouTube URLs
