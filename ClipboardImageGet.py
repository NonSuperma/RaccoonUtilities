from tkinter import Tk
from PIL import ImageGrab
from pathlib import Path
import subprocess
import sys
import ctypes
import time
import msvcrt


def scale_image(file_path: Path, new_dimentions: list[int], remove_old=False):
    class Output:
        def __init__(self, returncode: int, new_file_path):
            self.returncode = returncode
            self.newFilePath = new_file_path

    new_name = str(file_path.stem) + f'__{new_dimentions[0]}x{new_dimentions[1]}{str(file_path.suffix)}'
    new_file_path = Path(file_path.parent / new_name)

    scale = f'{str(new_dimentions[0])}:{str(new_dimentions[1])}'

    ffmpegOutput = subprocess.run(
        f'ffmpeg '
        f'-loglevel fatal '
        f'-y '
        f'-i "{file_path}" '
        f'-vf scale={scale} '
        f'-frames:v 1 '
        f'-update 1 '
        f'"{new_file_path}"'
    )
    if ffmpegOutput.returncode != 0:
        raise FfmpegGeneralError

    if remove_old:
        file_path.unlink()
        new_file_path.rename(file_path)
    return Output(new_file_path=new_file_path, returncode=1)


def ask_exit(message: str = '', timeout: int = 5) -> None:
    print(message)
    start = time.monotonic()
    last_shown = None

    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            break

        elapsed = time.monotonic() - start
        remaining = max(0, int(timeout - elapsed))

        if remaining != last_shown:
            print(f"\r" 
                  f"Press any key to exit "
                  f"(or wait {remaining} more seconds)…", end=' ')
            last_shown = remaining

        if elapsed >= timeout:
            break

        time.sleep(0.005)

    sys.exit()


def get_media_dimentions(file_path) -> list[int] | None:
    try:
        ffprobeOutput = subprocess.run(
            f'ffprobe '
            f'-v error '
            f'-select_streams v:0 '
            f'-show_entries stream=width,height -of csv=s=x:p=0 '
            f'"{file_path}"',
            shell=True, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    else:
        dimentions = [int(dimention) for dimention in ffprobeOutput.stdout.strip().split('x')]
    return dimentions


def count_open_explorer_downloads_windows():
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle('')
    explorer_windows = [window for window in windows if 'Pobrane' in window.title or 'Downloads' in window.title]
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


def crop_square_from_1920x1080_media(file_path: Path, output_name: str) -> None:
    output_path = file_path.parent / output_name
    subprocess.run(f'ffmpeg '
                   f'-y '
                   f'-i "{file_path}" '
                   f'-vf "crop=1080:1080:420:0" '
                   f'"{output_path}"',
                   shell=True, capture_output=True)
    return None


def main():
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
        scale_image(Path(f"{downloads_path}\\clipboard__square.png"), [500, 500])

    if count_open_explorer_downloads_windows() == 0:
        root = Tk()
        root.withdraw()
        root.lift()
        subprocess.run(f'explorer {downloads_path}')


if __name__ == '__main__':
    main()
