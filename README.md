# Disnake Music Bot

This is a Disnake music bot that plays music from YouTube.

## Features

*   Plays music from YouTube
*   Supports playlists
*   Has a queue
*   Has music controls (pause, resume, skip, stop, previous, volume, replay)
*   Automatically disconnects from the voice channel if it is alone for 30 seconds [[2]]

---

### **Autoplay**
When idle, the bot plays songs from its playlist.

---

### **Embed Structure**
The bot uses a dynamic embed with the following format:
**🎶 Now Playing**
[Song Title - Artist](link)
- *Artist*: [Name]
- *Requested by*: [@User]
- *Progress*: [ProgressBar] [Timestamp]
- *Queue*: [List of upcoming songs]
- *Last Played*: [Previously played tracks]
- *Thumbnail*: © 2025 Burger Byte Studio

---

### **Song Stats and Emoji Voting**
- **Stats Displayed**:
  - *Played*: Total plays.
  - *Requested*: User requests.
  - *Skipped*: Skip count.
  - *Last Played*: Date of prior play.
- **Emoji Voting**:
  - 👍: Like, 👎: Dislike, ⚠️: Report (with reason).
  - Votes inform the "song temperature" system [[8]].

---

### **Playlist Management**
- Stored in a `.txt` file.
- Supports adding YouTube links via commands.

---

### **Song Temperature System**
The bot adjusts music based on aggregated user feedback:
1. **Mood Mapping**:
   - Assign numerical "temperatures" to moods (e.g., *Sad*: 0.2, *Energetic*: 1.0) [[5]].
2. **Audio Feature Extraction**:
   - Analyze tempo, loudness, and spectral data to link audio characteristics to moods [[6]].
3. **Weighted Analysis**:
   - Combine features (e.g., tempo + energy) using predefined weights to calculate song "temperature" [[3]].
4. **Dynamic Adjustments**:
   - Transition between songs based on smoothed temperature trends [[7]].

---

### **Radio Host Mode**
Activated when the bot is alone:
- **TTS Commentary**: Simulates a radio host with song introductions, trivia, and news updates (tech, global events) [[9]].
- **Customization**: Admins can adjust tone (humorous/formal) and news categories. Commands for setting tone and news categories are restricted to administrators.

---

### **Dataset Creation for Mood Analysis**
*Objective*: Build a dataset to finetune the temperature model [[5]]:
1. **Define Moods**: Assign temperature values (e.g., *Calm*: 0.5, *Happy*: 0.8).
2. **Feature Extraction**: Use tools like `librosa` to extract tempo, energy, and spectral data [[6]].
3. **Map Features to Moods**: Link audio traits (e.g., high tempo → high temperature).
4. **Smooth Transitions**: Apply averaging to avoid abrupt mood shifts [[7]].
5. **Validation**: Test with sample tracks and refine weightings [[3]].

---

### **Implementation Notes**
- **Async Optimization**: Ensure non-blocking operations for simultaneous tasks (e.g., TTS + playback).
- **Data Security**: Store votes and reports in a secure database [[8]].
- **Updates**: Refresh playlists and retrain the model monthly to reflect user preferences [[2]].

---

**Sources**:
- Dataset strategies [[5]][[6]], documentation best practices [[1]][[3]], and async workflows [[8]].

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
