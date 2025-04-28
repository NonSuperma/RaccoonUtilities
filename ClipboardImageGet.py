from tkinter import Tk
from PIL import ImageGrab
import subprocess
import sys
import ctypes
import time
import msvcrt
import os.path

# pyinstaller ClipboardImageGet.py --noconsole --onefile --icon=5-1.ico

def get_media_dimentions(file_path) -> list[str] or None:
    ffprobeOutput = subprocess.run(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 {file_path}', shell=True, capture_output=True)
    if ffprobeOutput.returncode != 0:
        return None
    else:
        dimentions = ffprobeOutput.stdout.decode().strip().split('x')
        dimentions = [int(dimention) for dimention in dimentions]
    return dimentions

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

    image = ImageGrab.grabclipboard()

    if image is None:
        show_console()
        print("No image in clipboard nigga!")
        print("Press any key to exit...")

        start_time = time.time()
        while True:
            if msvcrt.kbhit() or time.time() - start_time > 5:
                break
            time.sleep(1)
        sys.exit()

    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    image.save(f'{downloads_path}\\clipboard.png')

    ss_dymentions = get_media_dimentions(f'{downloads_path}\\clipboard.png')
    if ss_dymentions == [1920, 1080]:
        crop_square_from_1920x1080_media(f'{downloads_path}\\clipboard.png', f'clipboard__square.png')
        subprocess.run(f'ffmpeg '
                       f'-y '
                       f'-i "{downloads_path}\\clipboard__square.png" '
                       f'-vf scale=500:500 '
                       f'"{downloads_path}\\clipboard__square500x500.png"',
                       shell=True, capture_output=True)

    if count_open_explorer_downloads_windows() < 1:
        root = Tk()
        root.withdraw()
        root.lift()
        subprocess.run(f'explorer {downloads_path}')

if __name__ == '__main__':
    main()