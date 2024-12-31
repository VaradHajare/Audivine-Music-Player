# Varad's Music Player

A modern YouTube music player built with Python and Tkinter that allows you to search, queue, and play music from YouTube. Features voice search and a sleek dark theme interface.

![image](https://github.com/user-attachments/assets/707c0486-34e4-4636-8f8c-24b627e24ed1)

## Features

- 🔍 Search and play music directly from YouTube
- 🎤 Voice search functionality
- 📋 Queue management with add/remove functionality
- ⏯️ Fluid playback controls (play/pause, previous, next, stop)
- 🔁 Queue replay toggle
- 🎚️ Volume control (syncs with system volume)
- ⌨️ Keyboard shortcuts for easy control
- 🎨 Modern dark theme interface
- 🖱️ Responsive buttons with hover effects

## Keyboard Shortcuts

- **Space**: Play/Pause
- **←**: Previous track/Restart current track
- **→**: Next track
- **↑**: Volume up
- **↓**: Volume down

## Requirements

- Python 3.6+
- Required Python packages:
  ```bash
  pygame
  yt-dlp
  youtube-search-python
  pycaw
  comtypes
  SpeechRecognition
  pyaudio
  ```
- FFmpeg

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
   ```bash
   pip install pygame yt-dlp youtube-search-python pycaw comtypes SpeechRecognition pyaudio
   ```
   
   For Windows users, if pyaudio installation fails:
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

3. Install FFmpeg:
   - Windows: Download from https://www.gyan.dev/ffmpeg/builds/ (get essentials build)
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

## Usage

1. Run the music player:
   ```bash
   python musicplayer.py
   ```
2. Search for songs using either:
   - Type in the search bar and click "Search & Add"
   - Click the microphone button (🎤) and speak your search query
3. Click songs in the queue to play them
4. Use the control buttons or keyboard shortcuts to control playback

## Features in Detail

### Search and Queue
- Text or voice search for songs
- Songs are automatically added to the queue
- First song starts playing automatically
- Remove songs using the ✕ button

### Playback Controls
- Play/Pause: Toggle playback of current song
- Previous: Go to previous song or restart current song
- Next: Skip to next song in queue
- Stop: Stop playback completely
- Fluid button animations and visual feedback

### Queue Management
- Click any song in the queue to play it
- Remove songs using the ✕ button next to each entry
- Toggle queue replay mode with the 🔁 button

### Volume Control
- Use the slider to adjust volume
- Volume changes affect both application and system volume
- Use Up/Down arrow keys for quick volume adjustment

### Voice Search
- Click the microphone button to start voice search
- Speak your search query clearly
- Visual feedback during recording and processing
- Automatically searches and adds the song to queue

## Notes

- The player requires an active internet connection
- Downloaded audio files are temporarily stored and automatically managed
- System volume control is currently supported on Windows only
- Voice search requires a working microphone

## License

This project is open source and available under the MIT License.

## Credits

Created by VaradHajare