from Raccoon.miscUtilities import seconds_to_hhmmss
from pathlib import Path
import subprocess


def get_media_duration(file_path: Path) -> str | None:
    try:
        ffprobeOutput = subprocess.run(
            f'ffprobe '
            f'-show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 '
            f'"{file_path}"',
            shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None

    return seconds_to_hhmmss(float(ffprobeOutput.stdout))
