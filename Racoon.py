import subprocess as sp
from tkinter import filedialog, Tk
import os


class RacoonErrors:

    class MissingInputError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    class DirectoryError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)


class RacoonMediaTools:

    def __init__(self, image_input_path: str, sound_input_paths: list[str]):
        self.image_input_path = image_input_path
        self.sound_input_paths = sound_input_paths

    def makeVideo(self, output_path: str or None):
        image_input_path = self.image_input_path
        if image_input_path == "":
            raise RacoonErrors.MissingInputError("No album cover selected")
        sound_input_paths = self.sound_input_paths
        if sound_input_paths == "":
            raise RacoonErrors.MissingInputError("No audio/s selected")

        if output_path is None:
            output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]

        if len(sound_input_paths) == 1:
            sound_input_paths = sound_input_paths[0]
            name = sound_input_paths[sound_input_paths.rfind('\\') + 1:sound_input_paths.rfind('.')]

            sp.run(f'ffmpeg '
                   f'-y '
                   f'-loop 1 '
                   f'-i "{image_input_path}" '
                   f'-i "{sound_input_paths}" '
                   f'-c:v libx264 '
                   f'-tune stillimage '
                   f'-c:a aac '
                   f'-b:a 256k '
                   f'-shortest '
                   f'-movflags +faststart '
                   f'-vf "format=yuv420p" '
                   f'-r 30 '
                   f'"{output_path}\\{name}.mp4"',
                   shell=True)

        else:
            names = []
            for INDEX in range(0, len(sound_input_paths)):
                names.append(
                    sound_input_paths[INDEX][sound_input_paths[INDEX].rfind("\\"):sound_input_paths[INDEX].rfind(".")])
            print(names)

            for INDEX in range(len(names)):
                sp.run(
                    f'ffmpeg '
                    f'-y '
                    f'-loglevel error'
                    f'-loop 1 '
                    f'-i "{image_input_path}" '
                    f'-i "{sound_input_paths[INDEX]}" '
                    f'-c:v libx264 '
                    f'-tune stillimage '
                    f'-c:a aac '
                    f'-b:a 256k '
                    f'-shortest '
                    f'-movflags +faststart '
                    f'-vf "format=yuv420p" '
                    f'-r 30 '
                    f'"{output_path}\\{names[INDEX]}.mp4"',
                    shell=True)

    def makeAlbum(self, output_path: str or None, final_filename: str):
        image_input_path = self.image_input_path
        if image_input_path == "":
            raise RacoonErrors.MissingInputError("No album cover selected")
        sound_input_paths = self.sound_input_paths
        if sound_input_paths == '':
            raise RacoonErrors.MissingInputError("No audio/s selected")
        if final_filename == '':
            raise RacoonErrors.MissingInputError("No final filename provided")

        if output_path is None:
            output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]
        print(output_path)

        inputPath = ''
        for i in sound_input_paths:
            inputPath += f'-i "{i.replace('/', '\\')}" '
        print(inputPath)

        preConcat = ''
        for i in range(0, len(sound_input_paths)):
            preConcat += f'[{i}:a]'

        extension = sound_input_paths[0][sound_input_paths[0].rfind('.'):]

        sp.run(f'ffmpeg '
               f'{inputPath}'  # No space here on purpose
               f'-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" '
               f'-b:a 256k '
               f'"{output_path}\\{final_filename + extension}"',
               shell=True)

        sp.run(f'ffmpeg '
               f'-y '
               f'-loglevel error '
               f'-r 1 '
               f'-loop 1 '
               f'-i "{image_input_path}" '
               f'-i "{output_path}\\{final_filename + extension}" '
               f'-c:v libx264 '
               f'-tune stillimage '
               f'-c:a aac '
               f'-b:a 256k '
               f'-shortest '
               f'-movflags +faststart '
               f'-vf "format=yuv420p" '
               f'-r 30 '
               f'"{output_path}\\{final_filename}.mp4"',
               shell=True)
    @staticmethod
    def askExit():
        input("Press enter to exit...")
        exit()

    @staticmethod
    def mkFolder(path, folder_name):
        try:
            if sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True).returncode != 0:
                raise RacoonErrors.DirectoryError(f'Folder {folder_name} already exists')
        except RacoonErrors.DirectoryError:
            print(f'Folder {folder_name} already exists')
        else:
            sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True)

    @staticmethod
    def winDirPath(message):
        root = Tk()
        root.withdraw()
        root.lift()
        tempPath = filedialog.askdirectory(title=message, parent=root).replace('/', '\\').strip()
        return tempPath

    @staticmethod
    def winFilePath(message):
        root = Tk()
        root.lift()
        root.withdraw()
        tempPath = filedialog.askopenfilename(title=message, parent=root).replace('/', '\\').strip()
        return tempPath

    @staticmethod
    def winFilesPath(message):
        root = Tk()
        root.lift()
        root.withdraw()
        tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
        for i in range(len(tempPaths)):
            tempPaths[i] = tempPaths[i].replace('/', '\\')
        return tempPaths

    @staticmethod
    def getBitrate(sound_input_path) -> dict[str, int] or None:
        if isinstance(sound_input_path, list):
            sound_input_path = sound_input_path[0]

        extensions = ['png', 'jpg', 'jpeg', 'webp']
        if sound_input_path[sound_input_path.rfind(".") + 1:] in extensions:
            return None

        value = sp.run(
            f'ffprobe '
            f'-v quiet '
            f'-select_streams a:0 '
            f'-show_entries stream=bit_rate '
            f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
        __type = 'bitrate'
        if value == 'N/A':
            value = sp.run(
                f'ffprobe '
                f'-v quiet '
                f'-select_streams a:0 '
                f'-show_entries stream=sample_rate '
                f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
                shell=True, capture_output=True).stdout.decode().strip()
            __type = 'samplerate'

        output = {
            __type: int(value)
        }
        return output

    @staticmethod
    def getAudioEncoding(file_path:str) -> str or None:
        if isinstance(file_path, list):
            file_path = file_path[0]
        extensions = ['png', 'jpg', 'jpeg', 'webp']
        if file_path[file_path.rfind(".") + 1:] in extensions:
            return None

        run = subprocess.run(
            f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file_path}"',
            shell=True, capture_output=True)
        return run.stdout.decode().strip()

    @staticmethod
    def count_open_windows(process_name: str) -> int or None:
        import psutil
        import pygetwindow as gw
        import win32gui
        import win32process
        open_windows = 0

        for window in gw.getAllWindows():
            hwnd = window._hWnd

            if not win32gui.IsWindowVisible(hwnd):
                continue

            cls = win32gui.GetClassName(hwnd)
            if cls not in ("CabinetWClass", "ExploreWClass"):
                continue

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                proc = psutil.Process(pid)
                if proc.name().lower() == process_name:
                    open_windows += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return open_windows

    @staticmethod
    def get_media_dimentions(file_path) -> list[str] or None:
        ffprobeOutput = sp.run(
            f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 {file_path}',
            shell=True, capture_output=True)
        if ffprobeOutput.returncode != 0:
            return None
        else:
            dimentions = ffprobeOutput.stdout.decode().strip().split('x')
            dimentions = [int(dimention) for dimention in dimentions]
        return dimentions