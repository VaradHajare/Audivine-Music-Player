# Varad's Music Player

A modern YouTube music player built with Python and Tkinter that allows you to search, queue, and play music from YouTube.

## Features

- 🔍 Search and play music directly from YouTube
- 📋 Queue management with add/remove functionality
- ⏯️ Basic playback controls (play/pause, previous, next, stop)
- 🔁 Queue replay toggle
- 🎚️ Volume control (syncs with system volume)
- ⌨️ Keyboard shortcuts for easy control
- 🎨 Modern dark theme interface

## Keyboard Shortcuts

- **Space**: Play/Pause
- **←**: Previous track/Restart current track
- **→**: Next track
- **↑**: Volume up
- **↓**: Volume down

## Requirements

- Python 3.6+
- Required Python packages:
  ```
  pygame
  yt-dlp
  youtube-search-python
  pycaw
  comtypes
  ```

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
   ```bash
   pip install pygame yt-dlp youtube-search-python pycaw comtypes
   ```
3. Ensure ffmpeg is installed and available in your system PATH or in the same directory as the script

## Usage

1. Run the music player:
   ```bash
   python musicplayer.py
   ```
2. Search for a song using the search bar
3. Double-click songs in the queue to play them
4. Use the control buttons or keyboard shortcuts to control playback

## Features in Detail

### Search and Queue
- Enter a song name in the search bar and click "Search & Add" or press Enter
- Songs are automatically added to the queue
- First song starts playing automatically

### Playback Controls
- Play/Pause: Toggle playback of current song
- Previous: Go to previous song or restart current song
- Next: Skip to next song in queue
- Stop: Stop playback completely

### Queue Management
- Double-click any song in the queue to play it
- Remove songs using the ✕ button next to each entry
- Toggle queue replay mode with the 🔁 button

### Volume Control
- Use the slider to adjust volume
- Volume changes affect both application and system volume
- Use Up/Down arrow keys for quick volume adjustment

## Notes

- The player requires an active internet connection
- Downloaded audio files are temporarily stored and automatically managed
- System volume control is currently supported on Windows only

## License

This project is open source and available under the MIT License.

## Credits

Created by VaradHajare
