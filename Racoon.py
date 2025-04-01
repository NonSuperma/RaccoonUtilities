import subprocess as sp
from tkinter import filedialog, Tk


class RacoonErrors:

    class MissingInputError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    class DirectoryError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)


class RacoonUtils:

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

            sp.run(
                f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths}" -c:v libx264 -acodec copy -b:a 320k -r 1 -shortest -vf format=yuv420p "{output_path}\\{name}.mp4"',
                shell=True)
        else:
            names = []
            for INDEX in range(0, len(sound_input_paths)):
                names.append(
                    sound_input_paths[INDEX][sound_input_paths[INDEX].rfind("\\"):sound_input_paths[INDEX].rfind(".")])
            print(names)

            for INDEX in range(len(names)):
                sp.run(
                    f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths[INDEX]}" -c:v libx264 -acodec copy -b:a 320k -r 1 -shortest -vf format=yuv420p "{output_path}\\{names[INDEX]}.mp4"',
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

        sp.run(
            f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" -b:a 320k "{output_path}\\output{extension}"',
            shell=True)
        sp.run(f'ren "{output_path}\\output{extension}" "{final_filename + extension}"', shell=True)

        sp.run(
            f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{output_path}\\{final_filename + extension}" -c:v libx264 -acodec copy -b:a 320k -r 1 -shortest -vf format=yuv420p "{output_path}\\{final_filename}.mp4"',
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
        root.lift()
        root.withdraw()
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
