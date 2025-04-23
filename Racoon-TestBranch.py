import subprocess as sp
import validators
from pathlib import Path
from tkinter import filedialog, Tk


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
        self.audio_paths = audio_paths

    def makeVideo(self, output_path: Path or None):
        # Audio and image paths are guaranteed to exist since they come from the class
        image_path = self.image_path
        audio_paths = self.audio_paths

        # Handle possible (?) missing input
        if output_path == '':
            raise REroors.MissingInputError('No output path')

        # Handle None as input of output_path
        if output_path is None:
            if type(audio_paths) is list:
                output_path = audio_paths[0][:audio_paths[0].rfind('\\')]
            else:
                output_path = audio_paths[:audio_paths.rfind('\\')]

        if type(audio_paths) is list:  # if there are multiple audios selected:
            for song in audio_paths:
                # 'ffmpeg
                # -r 1
                # -loop 1
                # -i "{image_input_path}"
                # -i "{sound_input_paths}"
                # -c:v libx264
                # -acodec copy
                # -r 1
                # -shortest
                # -vf format=yuv420p
                # "{output_path}\\{name}.mp4"')
                # ffmpeg -loop 1 -i input.jpg -i input.mp3 -c:v libx264 -tune stillimage -c:a copy -shortest -pix_fmt yuv420p output.mp4
                print(f'Processing {song[song.rfind('\\')+1:]} into a mp4 file...')
                sp.run(f'ffmpeg '
                       f'-r 1 '  # forces the framerate to be 1
                       f'-loop 1 '  # Tells ffmpeg to loop the input image until specified (forever untill stopped)
                       f'-i "{image_path}" '  # image input
                       f'-i "{song}" '  # ONE song input
                       f'-c:v libx264 '  # encoding for video, good for compatibility
                       f'-c:a copy '  # COPIES the encoding from the audio stream (meaning variables cannot be changed eg. bitrate)
                       f'-b:a 320000 '
                       f'-shortest '  # End the video when audio stream ends
                       f'-pix_fmt yuv420p '
                       f'{output_path}\\{song[song.rfind('\\')+1:song.rfind('.')]}.mp4',
                       shell=True,
                       capture_output=True)


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
            return tempPaths[0].replace('/', '\\')
        else:
            for i in range(len(tempPaths)):
                tempPaths[i] = tempPaths[i].replace('/', '\\')
            return tempPaths


image = WinTools.winFilePath('image')
audios = WinTools.winFilesPath("audios")
output = None

vid = MediaTools(image, audios)
vid.makeVideo(output)
