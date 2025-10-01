import subprocess as sp
from pathlib import Path
from typing import List
from Raccoon.errors import FfmpegGeneralError
from Raccoon.mediaUtilities import get_media_dimentions


def ScaleImage(file_path: Path, new_dimentions: str, remove_old=False):
    # Dimentions in this format;  1000:1000
    new_name = str(file_path.stem) + f'__{new_dimentions.replace(':', 'x')}{str(file_path.suffix)}'
    new_file_path = Path(file_path.parent / new_name)

    ffmpegOutput = sp.run(f'ffmpeg '
                          f'-loglevel fatal '
                          f'-y '
                          f'-i "{file_path}" '
                          f'-vf scale={new_dimentions} '
                          f'-frames:v 1 '
                          f'-update 1 '
                          f'"{new_file_path}"')
    if ffmpegOutput.returncode != 0:
        raise FfmpegGeneralError

    if remove_old:
        file_path.unlink()
        new_file_path.rename(file_path)
    return new_file_path


class ScaleToEvenResults:
    def __init__(self, returncode: int, dimensions: List[int]):
        self.returncode = returncode
        self.dimensions = dimensions


def ScaleToEven(file_path: Path, remove_old=True, alternatively_uneven=False) -> ScaleToEvenResults:
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
        dimentions = f'{new_dimentions[0]}:{new_dimentions[1]}'
        ScaleImage(file_path, dimentions, remove_old)
        return ScaleToEvenResults(returncode=0, dimensions=new_dimentions)
    else:
        return ScaleToEvenResults(returncode=1, dimensions=image_dimentions)
