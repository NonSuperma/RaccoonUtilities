import subprocess
from pathlib import Path
from typing import List
from Raccoon.errors import FfmpegGeneralError
from Raccoon.mediaUtilities import get_media_dimentions


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


def ScaleToEven(file_path: Path, remove_old=True, alternatively_uneven=False):
    class Output:
        def __init__(self, returncode: int, dimensions: List[int]):
            self.returncode = returncode
            self.dimensions = dimensions

    image_dimentions = get_media_dimentions(file_path)
    new_dimentions = []
    flagged = False
    if alternatively_uneven:
        for dimention in image_dimentions:
            if dimention % 2 == 0:
                flagged = True
                new_dimentions.append(dimention - 1)
            else:
                new_dimentions.append(dimention)
    else:
        for dimention in image_dimentions:
            if dimention % 2 != 0:
                flagged = True
                new_dimentions.append(dimention - 1)
            else:
                new_dimentions.append(dimention)
    if flagged:
        scale_image(file_path, new_dimentions, remove_old=remove_old)
        return Output(returncode=0, dimensions=new_dimentions)
    else:
        return Output(returncode=1, dimensions=image_dimentions)
