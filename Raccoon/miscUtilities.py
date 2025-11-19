from Raccoon.errors import *
from pathlib import Path
from typing import Dict, Any
import subprocess
import json
import sys
import os


def seconds_to_hhmmss(s: float) -> str:
    sign = "-" if s < 0 else ""
    s = abs(s)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f'{sign}{h:02d}:{m:02d}:{sec:06.3f}'


def hhmmss_to_seconds(timestamp: str) -> float:
    parts = timestamp.split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid format: expected 'HH:MM:SS.sss', got '{timestamp}'")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return hours * 3600 + minutes * 60 + seconds


def add_times(time_list: list[str] | list[float]) -> str:
    total = 0
    _format = 's' if time_list is list[str] else 'hh'
    for t in time_list:
        if _format == 's':
            total += t
        else:
            total += hhmmss_to_seconds(t)
    return seconds_to_hhmmss(total)


def resource_path(relative_path: str) -> str:

    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def console_clear_n(n: int) -> None:
    sys.stdout.flush()
    for i in range(n):
        sys.stdout.write('\x1b[1A\x1b[2K')
    sys.stdout.flush()


def get_bundled_file_path(file_name: str) -> Path:
    """
    Finds the path to the bundled ffmpeg.exe
    """
    if getattr(sys, 'frozen', False):
        # in a bundle
        # The path to the temp folder is sys._MEIPASS
        base_path = Path(sys._MEIPASS)
        file_path = base_path / file_name
    else:
        # normal .py script
        # Assume ffmpeg is in the system's PATH
        file_path = file_name

    return Path(file_path)


def get_media_file_data(file_path: Path) -> Dict[Any, Any] | None:
    extensions = ['png', 'jpg', 'jpeg', 'webp', 'ico', 'gif', 'bmp', 'tiff', 'svg', 'heic', 'avif']
    if file_path.suffix in extensions:
        return None

    ffprobeOutput_format = subprocess.run(
        f'ffprobe '
        f'-select_streams a '
        f'-show_entries '
        f'format=format_name,duration,size,bit_rate'
        f':format_tags '
        f'-print_format json '
        f'"{file_path}"',
        shell=True, capture_output=True, check=True)
    ffprobeOutputJson_format = json.loads(ffprobeOutput_format.stdout)

    ffprobeOutput_audio = subprocess.run(
                                    f'ffprobe '
                                    f'-select_streams a '
                                    f'-show_entries '
                                    f'format=format_name,duration,size,bit_rate'
                                    f':stream=index,codec_name,sample_rate,bits_per_raw_sample,channels,bit_rate'
                                    f':format_tags'
                                    f':stream_tags '
                                    f'-print_format json '
                                    f'"{file_path}"',
                                    shell=True, capture_output=True, check=True)
    ffprobeOutputJson_audio = json.loads(ffprobeOutput_audio.stdout)

    ffprobeOutput_video = subprocess.run(
                                    f'ffprobe '
                                    f'-select_streams v '
                                    f'-show_entries '
                                    f'stream=index,codec_name,width,height,pix_fmt'
                                    f':format_tags:stream_tags '
                                    f'-print_format json '
                                    f'"{file_path}"',
                                    shell=True, capture_output=True, check=True)

    ffprobeOutputJson_video = json.loads(ffprobeOutput_video.stdout)

    results = {}
    results.update({'format': ffprobeOutputJson_format})
    results.update({'video': ffprobeOutputJson_video['streams']})
    results.update({'audio': ffprobeOutputJson_audio['streams']})

    def convert_numeric_keys_values(d):
        new_dict = {}
        for key, value in d.items():
            if isinstance(key, str):
                try:
                    if key.isdigit():
                        key = int(key)
                    else:
                        key = float(key)
                except ValueError:
                    pass

            if isinstance(value, dict):
                value = convert_numeric_keys_values(value)

            elif isinstance(value, list):
                converted_list = []
                for item in value:
                    converted_list.append(convert_numeric_keys_values(item))
                value = converted_list

            elif isinstance(value, str):
                try:
                    if value.isdigit():
                        value = int(value)
                    else:
                        value = float(value)
                except ValueError:
                    pass

            new_dict[key] = value
        return new_dict

    results = convert_numeric_keys_values(results)

    return results
