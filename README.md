# 🌸 Uta Yuki - Your Anime-Inspired Music Companion 🎶

Welcome to **Uta Yuki**, a Discord bot that brings the magic of anime and music together! Whether you're hosting a virtual karaoke night, jamming to your favorite tunes, or just chilling with friends, Uta Yuki is here to make your experience unforgettable. With a sprinkle of anime charm and a dash of fun, Uta Yuki is your go-to music bot for all things melodic and magical.

---

## 🎵 Features

### 🎧 **Music Player**

- **Play your favorite songs**: Queue up tracks from YouTube and enjoy high-quality audio streaming.
- **Interactive controls**: Pause, resume, skip, replay, and adjust volume with easy-to-use buttons.
- **Playlist support**: Load up your custom playlists and let Uta Yuki shuffle through them for endless entertainment.
- **Progress bar**: Keep track of your song's progress with a visually appealing progress bar.

### 🐷 **Pig Latin Fun**

- **To Pig Latin**: Convert any text into Pig Latin for some lighthearted fun! Perfect for anime-inspired roleplay or just goofing around with friends.

### 🎨 **Anime Aesthetic**

- **Beautiful embeds**: Enjoy visually stunning embeds with anime-inspired designs.
- **Customizable signature**: Add your own flair with a custom signature in the bot's messages.

### 🛠️ **Easy Setup**

- **Simple installation**: Just clone the repo, set up your virtual environment, and you're ready to go!
- **Customizable configuration**: Easily configure the bot to suit your server's needs.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- A Discord bot token (get one from the [Discord Developer Portal](https://discord.com/developers/applications))
- `yt-dlp` for YouTube audio streaming
- `disnake` for Discord API interactions

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-repo/uta-yuki.git
   cd uta-yuki
   ```

2. **Set up a virtual environment**:

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure the bot**:

   - Open `config.py` and add your Discord bot token.
   - Customize `TEST_GUILD_IDS` if you want to restrict slash commands to specific guilds.

6. **Run the bot**:
   ```bash
   python bot.py
   ```

---

## 🎨 Customization

### Playlist

- Add your favorite songs to `playlist.txt` in the following format:
  ```txt
  [default]
  https://www.youtube.com/watch?v=KLm8JCjfWVs ; In Too Deep ~ Battle Tapes
  https://www.youtube.com/watch?v=VxY5xLKipp4 ; Explosion ~ Kalwi & Remi
  ```

### Signature

- Customize the bot's signature by editing `signature.txt`:
  ```txt
  (c) 2025 Your Awesome Server
  ```

---

## 🎮 Commands

### Music Commands

- **`/play [url]`**: Play a song from YouTube.
- **`/pause`**: Pause the current song.
- **`/resume`**: Resume the paused song.
- **`/skip`**: Skip to the next song in the queue.
- **`/stop`**: Stop the music and disconnect the bot.

### Fun Commands

- **`/to_pig_latin [text]`**: Convert text to Pig Latin.

---

## 🌟 Why Uta Yuki?

Uta Yuki is more than just a music bot—it's a companion that brings joy and excitement to your Discord server. With its anime-inspired design and user-friendly features, Uta Yuki is perfect for anime lovers, music enthusiasts, and anyone looking to add a touch of magic to their server.

---

## 📜 License

Uta Yuki is licensed under the **Open Helping Development License (OHDL)**. This means the software and any derivative works must remain open source, freely available to the public, and never monetized. For more details, check out the [LICENSE](LICENSE) file.

---

## 💖 Support

If you enjoy using Uta Yuki, consider giving the repository a ⭐ on GitHub! Your support helps us keep the project alive and thriving.

---

## 🎉 Let's Get Started!

Ready to bring Uta Yuki to your server? Follow the installation steps above, and let the music and anime magic begin!

```bash
python bot.py
```

---

🌸 **Uta Yuki** - Where music meets anime, and fun never ends! 🌸
