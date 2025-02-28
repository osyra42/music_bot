# Disnake Music Bot

This is a Disnake music bot that plays music from YouTube.

## Features

*   Plays music from YouTube
*   Supports playlists
*   Has a queue
*   Has music controls (pause, resume, skip, stop, previous, volume, replay)
*   Automatically disconnects from the voice channel if it is alone for 30 seconds

## Installation

1.  Install Python 3.8 or higher.
2.  Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```
3.  Create a file named `secret.py` and add your bot token and test guild ID:

    ```python
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    TEST_GUILD_ID = YOUR_TEST_GUILD_ID
    ```
4.  Fill in the `playlist.txt` file with URLs.

## Usage

1.  Run the bot:

    ```bash
    python main.py
    ```
2.  Use the slash commands in your Disnake server to control the bot.

## Commands

*   `/join`: Joins the voice channel.
*   `/leave`: Leaves the voice channel.
*   `/play`: Plays audio from a YouTube URL.
*   `/stop`: Stops playing audio.
*   `/disconnect`: Disconnects the bot from the voice channel.

## Contributing

Feel free to contribute to this project by submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
