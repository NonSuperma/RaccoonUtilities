from pathlib import Path
import subprocess as sp


def get_media_dimentions(file_path) -> list[str] or None:
    ffprobeOutput = sp.run(
        f'ffprobe '
        f'-v error '
        f'-select_streams v:0 '
        f'-show_entries stream=width,height -of csv=s=x:p=0 '
        f'"{file_path}"',
        shell=True, capture_output=True)
    if ffprobeOutput.returncode != 0:
        return None
    else:
        dimentions = ffprobeOutput.stdout.decode().strip().split('x')
        dimentions = [int(dimention) for dimention in dimentions]
    return dimentions

