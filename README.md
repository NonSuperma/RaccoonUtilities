# RaccoonUtilities

A collection of small utilities for audio/video editing and system automation.

### Core Library: `Raccoon`

A set of reusable utilities for audio, image, and media processing:

- **audioUtilities** – Get media duration and audio information
- **imageUtilities** – Scale images, adjust dimensions to even numbers
- **mediaUtilities** – Extract media dimensions from audio/video files
- **windowsUtilities** – Windows-specific file dialogs and system operations
- **ffmpegUtilities** – FFmpeg wrapper utilities
- **miscUtilities** – Helpful utility functions

### Standalone Tools

#### Raccoon Chat
Gemini API interface in the form of a chat. Chats can be normal or roleplay-based with the ability to specify the character played by ai in detail. Built-in spell-checking, customizable themes, and persistent chat history. There is also an automated history compression feature that heavely saves on tokens.

```bash
python Raccoon_Chat/raccoon_chat.py
```

#### Album Manager
Batch process and organize audio files. Convert, encode, and manage music albums with ffmpeg.

```bash
python AlbumManager.py
```

#### Remove Background
Remove image backgrounds using AI. Select images from your system and instantly remove backgrounds with a clean, modern interface. WIP, mid results rn.

```bash
python RemoveBG/remove_bg.py
```

#### Video Cutting Tool
Interactive video cutting with preview. Mark start/end points in a video player and extract clips without re-encoding (although this limits the precision of the timestamps on most video formats). 

```bash
python vid_cut.py
```

#### Stream Downloader
Stream overwiew tool. Allows for opening clean, snapable mpv windows with the streams as well as selective recording.

```bash
python stream_downloader_V2/stream_downloader_V2.py
```

#### Clipboard Image Capture
Grab images from clipboard and save them to disk quickly.

```bash
python ClipboardImageGet.py
```

#### Monitor Switch
Switch between monitors and manage display layouts.

```bash
python MonitorSwitch.py
```

#### Raccoon Menu
A quick-access menu system with hotkey support (Shift+Space to toggle). WIP Proof of concept.

```bash
python RaccoonMenu.py
```

## Requirements

### Python
- Python 3.10+

### Dependencies
Install via pip:

```bash
pip install -r requirements.txt
```

Key packages:
- `google-generativeai` – For AI chat features
- `pillow` – Image processing
- `rembg` – Background removal
- `pyperclip` – Clipboard operations
- `customtkinter` – Modern UI toolkit
- `pyspellchecker` – Spell checking
- `mpv` – Video playback
- `pyaudio` – Audio processing
- `colorama` – Terminal colors
- `keyboard` – Hotkey detection

### External Tools
Some utilities require ffmpeg:

```bash
# Download ffmpeg binaries and place in project root
# Or install via package manager:
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: apt-get install ffmpeg
```

For Raccoon Chat, you'll need a Google API key:
1. Get a key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Save to `Raccoon_Chat/api_key.txt`

## Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/NonSuperma/RaccoonUtilities.git
cd RaccoonUtilities
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run any utility**
```bash
python Raccoon_Chat/raccoon_chat.py
python AlbumManager.py
python RemoveBG/remove_bg.py
# ... or any other tool
```

## Project Structure

```
RaccoonUtilities/
├── Raccoon/                    # Core utility library
│   ├── audioUtilities.py
│   ├── imageUtilities.py
│   ├── mediaUtilities.py
│   ├── windowsUtilities.py
│   └── ...
├── Raccoon_Chat/              # AI chat application
├── RemoveBG/                  # Background removal tool
├── stream_downloader_V2/       # Video stream downloader
├── Playground/                # Experimental utilities
└── MiscScripts/               # One-off helper scripts
```

## Usage Examples

### Using the Raccoon Library

```python
from Raccoon.imageUtilities import scale_image
from Raccoon.mediaUtilities import get_media_dimentions
from pathlib import Path

# Get video dimensions
dims = get_media_dimentions(Path("video.mp4"))
print(f"Video is {dims[0]}x{dims[1]}")

# Scale an image
scale_image(Path("image.jpg"), [1920, 1080])
```

### Running Tools

Each tool is standalone and can be run directly:

```bash
# Chat with AI
python Raccoon_Chat/raccoon_chat.py

# Process video streams
python stream_downloader_V2/stream_downloader_V2.py

# Remove backgrounds from images
python RemoveBG/remove_bg.py
```

## Notes

- Most tools are Windows-optimized but contain cross-platform fallbacks
- Some features require external tools (ffmpeg, rembg models)
- UI-based tools use tkinter/customtkinter for a modern dark interface
- All chat history and configurations are stored locally

## License

See [LICENSE](LICENSE) for details.

---

Built by a student that doesn't know what he's doing