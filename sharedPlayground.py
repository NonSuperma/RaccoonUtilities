from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.windowsUtilities import *
from rich.console import Console
from rich.panel import Panel
import subprocess
import time
import msvcrt
import sys
import configparser
from pathlib import Path
import json
from colorama import Fore

mvb_clrln = '\r\033[2K'


def subprocess_run_timecount(cmd, message: str = 'Running...', **kwargs):
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, **kwargs)

    while True:
        current_time = time.time()
        if process.poll() is not None:
            print(f'{mvb_clrln}{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}')
            break

        elapsed = round(current_time - start_time, 1)
        print(f' {Fore.LIGHTYELLOW_EX}{message} ({elapsed}s){Fore.RESET}', end='\r', flush=True)
        time.sleep(0.1)


def subprocess_run_with_spinner(cmd, progress_message='Running...', **kwargs):
    """
    Executes a subprocess command while displaying a terminal spinner.

    Args:
        cmd (list): The command and arguments to execute.
        progress_message (str): The text to display next to the spinner.

    Raises:
        subprocess.CalledProcessError: If the subprocess exits with a non-zero code.
    """
    console = Console()

    kwargs.setdefault('spinner', 'dots12')
    kwargs.setdefault('spinner_style', 'yellow')
    with console.status(f'{progress_message}', **kwargs):
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        stdout_text, _ = process.communicate()
        exit_code = process.returncode

    if exit_code != 0:
        raise subprocess.CalledProcessError(
            returncode=exit_code,
            cmd=cmd,
            output=stdout_text
        )


file_path = win_file_path()
cover_path = win_file_path('cover')
mp4_output_path = file_path.parent / file_path.with_suffix('.mp4').name
ffmpeg_exe = r'SourceFiles\ffmpeg.exe'
cmd = [ffmpeg_exe, '-y', '-nostdin',
       '-loglevel', 'error',
       '-loop', '1',
       '-framerate', '1',
       '-i', str(cover_path),
       '-i', str(file_path),
       '-c:v', 'libx264',
       '-tune', 'stillimage',
       '-c:a', 'copy',
       '-pix_fmt', 'yuv420p',
       '-shortest',
       '-movflags', '+faststart',
       str(mp4_output_path)]

# subprocess_run_timecount(cmd, text=True)