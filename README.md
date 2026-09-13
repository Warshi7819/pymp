# pyMP - Python Music Player

An asynchronous event-based music player built with Python, wxPython, and pygame-ce.

Initially this project was started by myself back in the early 2000s. Hosted on the defacto open 
source hub at the time - SourceForge. Actually you can still find the original python 2.0 code there:
- [SourceForge pyMP project page](https://sourceforge.net/projects/pyplayer/)

Thought I would bring it back to life and make it available here on GitHub to celebrate the past.

## Features

- Skinnable GUI with XML-based skin configuration
- Playlist management (add files, directories, import/export)
- Global hotkeys for playback control
- Taskbar icon integration
- MP3 playback with ID3 tag support
- TCP/IP streaming support
- Configurable settings (skin, hotkeys, stay-on-top, etc.)

## Requirements
The following deps where present during the migration from Python 2 to Python 3 and are required to run the player:

- Python 3.14.6+
- wxPython 4.3.1+
- pygame-ce 2.5.8+ 
  - pygame Community Edition


Install dependencies:

```bash
pip install wxpython pygame-ce
```

## Running

1. Enter the `src` directory
2. Run the player:

```bash
python pymp.py
```

## Hotkeys

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+P | Play |
| Ctrl+Shift+S | Stop |
| Ctrl+Shift+N | Next track |
| Ctrl+Shift+B | Previous track |
| Ctrl+Shift+W | Pause/Unpause |
| Ctrl+Shift+D | Show/Hide player |

## Project Structure

```
pymp/
├── src/           # Source code
│   ├── pymp.py    # Entry point
│   ├── skin/      # Skin definitions (XML + images)
│   └── ...
├── images/        # Application images
├── doc/           # Documentation
└── mp3/           # Sample MP3 files
```

## License

GNU General Public License v3.0 - see [LICENSE.txt](LICENSE.txt) for details.

## Credits

Originally created by Rune Devik (2004). Updated to Python 3 with pygame-ce for audio playback in 2026.
