import subprocess as sp
import validators
from pathlib import Path

class REroors:

    class MissingInputError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    class DirectoryError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

class MediaTools:
    def __init__(self, image_path: Path, audio_paths: list[Path] or Path):
        self.image_path = image_path
        self.audio_path = audio_paths

    def makeVideo(self, output_path: Path or None):
        self.output_path = output_path





class WinTools:

    @staticmethod
    def mkFolder(path: Path, folder_name: str) -> None:
        try:
            if sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True).returncode != 0:
                raise RacoonErrors.DirectoryError(f'Folder {folder_name} already exists')
        except RacoonErrors.DirectoryError:
            print(f'Folder {folder_name} already exists')
        else:
            sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True)

    @staticmethod
    def winDirPath(message: str):
        root = Tk()
        root.lift()
        root.withdraw()
        tempPath = filedialog.askdirectory(title=message, parent=root).replace('/', '\\').strip()
        return tempPath

    @staticmethod
    def winFilePath(message: str):
        root = Tk()
        root.lift()
        root.withdraw()
        tempPath = filedialog.askopenfilename(title=message, parent=root).replace('/', '\\').strip()
        return tempPath

    @staticmethod
    def winFilesPath(message: str):
        root = Tk()
        root.lift()
        root.withdraw()
        tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
        if len(tempPaths) == 1:
            return tempPaths[0]
        else:
            for i in range(len(tempPaths)):
                tempPaths[i] = tempPaths[i].replace('/', '\\')
            return tempPaths