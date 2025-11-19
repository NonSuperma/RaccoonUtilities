import sys
from pathlib import Path


def get_ffmpeg_path():
    """
    Finds the path to the bundled ffmpeg.exe
    """
    if getattr(sys, 'frozen', False):
        # in a bundle
        # The path to the temp folder is sys._MEIPASS
        base_path = Path(sys._MEIPASS)
        ffmpeg_path = base_path / "ffmpeg.exe"
    else:
        # normal .py script
        # Assume ffmpeg is in the system's PATH
        ffmpeg_path = "ffmpeg"

    return str(ffmpeg_path)