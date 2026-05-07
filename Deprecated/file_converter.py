from tkinter import filedialog, Tk
from pathlib import Path
from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.errors import *
import subprocess
import playsound3


def convert_file(file_path: Path, new_extension, delete_old: bool = False):



def convert(path_to_file: Path, newExtension: str):
        if path_to_file.suffix == newExtension:
            return

        emptyName = path_to_file.with_suffix('')
        extensions = ['.png', '.jpg', '.jpeg', '.webp', '.ico', '.gif', '.bmp', '.tiff', '.svg', '.heic', '.avif']

        if path_to_file.suffix.lower() in extensions:
            if newExtension.lower() == '.ico':
                subprocess.run(
                    f'ffmpeg -y -i "{path_to_file}" -vf "scale=256:256:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2" "{emptyName}{newExtension}"',
                    shell=True, capture_output=True
                )
            else:
                subprocess.run(
                    f'ffmpeg -y -i "{path_to_file}" -update 1 -frames:v 1 "{emptyName}{newExtension}"',






def main():
    track_paths = win_files_path()

    conver_file(track_paths, input(f'new extension: '))


if __name__ == '__main__':
    main()

    script_dir = Path(__file__).parent
    sound_path = script_dir.parent / 'SourceFiles' / 'au5-1.mp3'

    playsound3.playsound(str(sound_path))
