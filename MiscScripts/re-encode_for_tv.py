from Raccoon.windowsUtilities import win_files_path
from Raccoon.windowsUtilities import ask_exit
from Raccoon.ffmpegUtilities import get_ffmpeg_path
from Raccoon.errors import MissingInputError
from pathlib import Path
from colorama import Fore
import subprocess


def main():
    try:
        input_paths = win_files_path("videos")
    except MissingInputError:
        ask_exit(f'{Fore.LIGHTRED_EX}User closed the window{Fore.RESET}')

    extensions = ['.mp4', '.webm', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.3gp', '.mpg', '.ogv']
    for path in input_paths:
        if path.suffix not in extensions:
            print(f'{Fore.LIGHTYELLOW_EX}Selected path: {Fore.LIGHTCYAN_EX}"{path}" {Fore.LIGHTYELLOW_EX}is not a video, dropping...{Fore.RESET}')
            input_paths.pop(input_paths.index(path))

    if not input_paths:
        ask_exit(f'{Fore.LIGHTRED_EX}No videos detected{Fore.RESET}')

    directory = input_paths[0].parent

    ffmpeg_executable = get_ffmpeg_path()

    if ffmpeg_executable != "ffmpeg" and not Path(ffmpeg_executable).exists():
        ask_exit(f'{Fore.LIGHTRED_EX}Error: Bundled ffmpeg.exe not found at {ffmpeg_executable}')

    for path in input_paths:
        output_name = 'kompatybilne_' + path.name
        output_path = directory / output_name

        if len(path.name) > 30:
            print(f'Processing: '
                  f'{Fore.LIGHTCYAN_EX}{path.name[:30] + '(...)' + path.suffix}{Fore.RESET} '
                  f'-> {Fore.LIGHTCYAN_EX}{output_name}{Fore.RESET}')
        else:
            print(f'Processing: '
                  f'{Fore.LIGHTCYAN_EX}{path.name}{Fore.RESET} '
                  f'-> {Fore.LIGHTCYAN_EX}{output_name}{Fore.RESET}')

        cmd = [
            ffmpeg_executable,
            '-y',
            '-i', str(path),
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264', '-profile:v', 'main', '-level', '4.0',
            '-pix_fmt', 'yuv420p', '-crf', '22',
            '-c:a', 'aac', '-b:a', '96k',
            '-loglevel', 'error',
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f'{Fore.LIGHTGREEN_EX}Successfully converted to: {Fore.LIGHTCYAN_EX}{output_name}{Fore.RESET}')
        except subprocess.CalledProcessError as e:
            print(f'{Fore.LIGHTRED_EX}Error processing file: {Fore.LIGHTCYAN_EX}{path.name}{Fore.RESET}\n'
                  f'Error contents:')
            print(e.stderr)


if __name__ == '__main__':
    main()
    ask_exit(timeout=10)
