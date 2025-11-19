from Raccoon.mediaUtilities import get_media_dimentions
from Raccoon.windowsUtilities import ask_exit
from Raccoon.imageUtilities import scale_image
from pathlib import Path
from tkinter import Tk
from PIL import ImageGrab
import subprocess
import sys
import ctypes
import time
import msvcrt
import os.path


def count_open_explorer_downloads_windows():
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle('')
    explorer_windows = [window for window in windows if 'Downloads' in window.title]
    return len(explorer_windows)


def show_console():
    root = Tk()
    root.withdraw()
    root.lift()
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open('CONOUT$', 'w')
    sys.stderr = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')


def hide_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


def crop_square_from_1920x1080_media(file_path, output_name) -> None:
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    subprocess.run(f'ffmpeg '
                   f'-y '
                   f'-i "{file_path}" '
                   f'-vf "crop=1080:1080:420:0" '
                   f'"{downloads_path}\\{output_name}"',
                   shell=True, capture_output=True)
    return None


def main():
    hide_console()
    hide_console()
    image = ImageGrab.grabclipboard()

    if image is None:
        show_console()
        ask_exit("No image in clipboard nigga!")

    downloads_path = Path.home() / 'Downloads'
    filename = 'clipboard'
    number = 1
    pathToFile = (downloads_path / filename).with_suffix('.png')

    while pathToFile.exists():
        filename = 'clipboard' + str(number)
        pathToFile = (downloads_path / filename).with_suffix('.png')
        number += 1

    image.save(pathToFile)

    ss_dymentions = get_media_dimentions(pathToFile)

    if ss_dymentions == [1920, 1080]:
        crop_square_from_1920x1080_media(pathToFile, f'clipboard__square.png')
        scale_image(Path(f"{downloads_path}\\clipboard__square.png"), '500:500')

    if count_open_explorer_downloads_windows() < 1:
        root = Tk()
        root.withdraw()
        root.lift()
        subprocess.run(f'explorer {downloads_path}')


if __name__ == '__main__':
    main()
