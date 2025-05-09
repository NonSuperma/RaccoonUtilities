import subprocess as sp
from tkinter import filedialog, Tk, BooleanVar
from typing import Optional, List
from colorama import init, Fore, Back, Style
from datetime import datetime, timedelta
import os
import msvcrt
import time
import sys
from pathlib import Path


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

    def __init__(self, image_input_path: Path, sound_input_paths: list[Path]) -> None:
        self.image_input_path: Path = image_input_path
        self.sound_input_paths: list[Path] = sound_input_paths

    @staticmethod
    def parse_time_string(time_str):
        dt = datetime.strptime(time_str, "%H:%M:%S.%f")
        return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)

    @staticmethod
    def add_times(time_list):
        total = timedelta()
        for t in time_list:
            total += RacoonMediaTools.parse_time_string(t)
        return str(total)

    @staticmethod
    def askExit(message: str) -> None:
        print(message)
        print("Press any key to exit...")

        start_time = time.time()
        while True:
            if msvcrt.kbhit() or time.time() - start_time > 5:
                break
            time.sleep(1)
        sys.exit()

    @staticmethod
    def mkFolder(path: Path, folder_name: str) -> None:
        if Path.exists(path):
            pass

        os.makedirs(Path.joinpath(path, folder_name), exist_ok=True)

    @staticmethod
    def winDirPath(message: str) -> Path:
        root = Tk()
        root.withdraw()
        root.lift()

        file_path = Path(filedialog.askdirectory(title=message, parent=root))
        if not file_path:
            raise RacoonErrors.MissingInputError('User closed the window')

        return file_path

    @staticmethod
    def winFilePath(message: str) -> Path:
        root = Tk()
        root.lift()
        root.withdraw()
        file_path = Path(filedialog.askopenfilename(title=message, parent=root))
        if not file_path:
            raise RacoonErrors.MissingInputError('User closed the window')

        return file_path

    @staticmethod
    def winFilesPath(message: str) -> list[Path]:
        root = Tk()
        root.lift()
        root.withdraw()
        file_paths = list(filedialog.askopenfilenames(title=message, parent=root))

        if not file_paths:
            raise RacoonErrors.MissingInputError('User closed the window')

        path_objects = [Path(p) for p in file_paths]
        return path_objects

    @staticmethod
    def getBitrate(sound_input_path: Path) -> dict[str, int] or None:
        if sound_input_path is list:
            sound_input_path = sound_input_path[0]

        extensions = ['png', 'jpg', 'jpeg', 'webp']
        if sound_input_path.suffix in extensions:
            return None

        value = sp.run(
            f'ffprobe '
            f'-v quiet '
            f'-select_streams a:0 '
            f'-show_entries stream=bit_rate '
            f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
        _type = 'bitrate'
        if value == 'N/A':
            value = sp.run(
                f'ffprobe '
                f'-v quiet '
                f'-select_streams a:0 '
                f'-show_entries stream=sample_rate '
                f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
                shell=True, capture_output=True).stdout.decode().strip()
            _type = 'samplerate'

        output = {
            _type: int(value)
        }
        return output

    @staticmethod
    def getAudioEncoding(file_path: Path) -> str or None:
        if isinstance(file_path, list):
            file_path = file_path[0]
        extensions = ['.png', '.jpg', '.jpeg', '.webp']
        if file_path.suffix in extensions:
            return None

        ffprobeOutput = sp.run(
            f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file_path}"',
            shell=True, capture_output=True)
        return ffprobeOutput.stdout.decode().strip()

    @staticmethod
    def getAudioDuration(file_path: Path) -> float or None:
        ffprobeOutput = sp.run(
            f'ffprobe -sexagesimal -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"',
            shell=True, capture_output=True)
        if ffprobeOutput.returncode != 0:
            print(ffprobeOutput.stdout.decode())
            return None
        else:
            return ffprobeOutput.stdout.decode().strip()

    @staticmethod
    def count_open_windows(process_name: str) -> int or None:
        import psutil
        import pygetwindow as gw
        import win32gui
        import win32process
        open_windows = 0

        for window in gw.getAllWindows():
            hwnd = window.handle

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

    def makeVideo(self, output_path: Optional[Path], lenght_check: BooleanVar, pure_audio: BooleanVar):
        init(autoreset=True)
        image_input_path: Path = self.image_input_path
        if image_input_path == "":
            raise RacoonErrors.MissingInputError("No album cover selected")
        sound_input_paths: list[Path] = self.sound_input_paths
        if sound_input_paths == "":
            raise RacoonErrors.MissingInputError("No audio/s selected")

        if output_path is None:
            output_path = sound_input_paths[0].parent

        if len(sound_input_paths) == 1:
            sound_input_paths: Path = Path(sound_input_paths[0])
            name = sound_input_paths.stem

            duration = RacoonMediaTools.getAudioDuration(sound_input_paths)
            if pure_audio:
                ffmpegOutput = sp.run(f'ffmpeg '
                                      # f'-loglevel fatal '
                                      f'-y '
                                      f'-loop 1 '
                                      f'-framerate 1 '
                                      f'-i "{image_input_path}" '
                                      f'-i "{sound_input_paths}" '
                                      f'-c:v libx264 '
                                      f'-tune stillimage '
                                      f'-c:a copy '
                                      f'-t {duration} '
                                      f'-movflags +faststart '
                                      f'-vf "format=yuv420p" '
                                      f'-r 1 '
                                      f'"{output_path}\\{name}.mp4"',
                                      shell=True, capture_output=False)

            else:
                ffmpegOutput = sp.run(f'ffmpeg '
                                      # f'-loglevel fatal '
                                      f'-y '
                                      f'-loop 1 '
                                      f'-framerate 1 '
                                      f'-i "{image_input_path}" '
                                      f'-i "{sound_input_paths}" '
                                      f'-c:v libx264 '
                                      f'-tune stillimage '
                                      f'-c:a aac '
                                      f'-t {duration} '
                                      f'-movflags +faststart '
                                      f'-vf "format=yuv420p" '
                                      f'-r 1 '
                                      f'"{output_path}\\{name}.mp4"',
                                      shell=True, capture_output=False)

            if lenght_check:
                oryginalDuration = RacoonMediaTools.getAudioDuration(sound_input_paths)
                converterDuration = RacoonMediaTools.getAudioDuration(Path(f'{output_path}\\{name}.mp4'))
                if oryginalDuration != converterDuration:
                    temp_path = sound_input_paths.stem + "_temp" + sound_input_paths.suffix
                    sp.run(
                        f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_paths}" -c copy "{temp_path}"',
                        shell=True)
                    os.replace(temp_path, sound_input_paths)
            return ffmpegOutput

        else:
            paths_to_file_no_extension = []
            for INDEX in range(0, len(sound_input_paths)):
                paths_to_file_no_extension.append(sound_input_paths[INDEX].stem)

            for INDEX in range(len(paths_to_file_no_extension)):
                ffmpegOutput = []
                ffmpegOutputPart = sp.run(
                    f'ffmpeg '
                    f'-y '
                    # f'-loglevel warning '
                    f'-loop 1 '
                    f'-i "{image_input_path}" '
                    f'-i "{sound_input_paths[INDEX]}" '
                    f'-c:v libx264 '
                    f'-tune stillimage '
                    f'-c:a opus '
                    f'-b:a 256k '
                    f'-shortest '
                    f'-movflags +faststart '
                    f'-vf "format=yuv420p" '
                    f'-r 30 '
                    f'"{Path.joinpath(output_path, paths_to_file_no_extension[INDEX]).with_suffix('.mp4')}"',
                    shell=True)

                if lenght_check:
                    oryginalDuration = RacoonMediaTools.getAudioDuration(sound_input_paths[INDEX])
                    converterDuration = RacoonMediaTools.getAudioDuration(
                        Path.joinpath(output_path, paths_to_file_no_extension[INDEX]).with_suffix('.mp4'))

                    if oryginalDuration != converterDuration:
                        temp_path = sound_input_paths[INDEX].stem + "_temp" + sound_input_paths[INDEX].suffix
                        sp.run(
                            f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_paths[INDEX]}" -c copy "{temp_path}"',
                            shell=True)
                        os.replace(temp_path, sound_input_paths[INDEX])
                    ffmpegOutput.append(ffmpegOutputPart)

            return ffmpegOutput

    def makeAlbum(self, output_path: str or None, final_filename: str):
        init(autoreset=True)

        if output_path == None:
            output_path = self.sound_input_paths[0].parent
            print(output_path)

        def concad_audio(audio_paths: list[Path]):
            oryginal_durations = []
            for audio_path in audio_paths:
                oryginal_durations.append(RacoonMediaTools.getAudioDuration(audio_path))

            for audio_path in audio_paths:
                audio_path_converted = audio_path.with_suffix('.aac')
                test = True




                sp.run(f'ffmpeg '
                      f'-i "{audio_path}" '
                      f'-b:a 270k '
                      f'"{audio_path_converted}"',
                      shell=True, capture_output=True)
                if not test:
                    audio_path.unlink()

            for index in range(len(audio_paths)):
                audio_paths[index] = audio_paths[index].with_suffix('.aac')

            with open(output_path / 'audio_input_list.txt', 'w+', encoding='utf-8') as audio_input_list:
                for audio_path in audio_paths:
                    audio_input_list.write(f"file '{audio_path}'\n")

            audio_path_concaded = Path(output_path / final_filename).with_suffix('.aac')
            sp.run(f'ffmpeg '
                   f'-f concat '
                   f'-safe 0 '
                   f'-i "{Path.joinpath(output_path, 'audio_input_list.txt')}" '
                   f'-c copy '
                   f'"{audio_path_concaded}"',
                   shell=True, capture_output=False)

            Path(Path.joinpath(output_path, 'audio_input_list.txt')).unlink()

            if test:
                converted_durations = []
                for audio_path in audio_paths:
                    converted_durations.append(RacoonMediaTools.getAudioDuration(audio_path))
                converted_duration = RacoonMediaTools.add_times(converted_durations)
                final_duration = RacoonMediaTools.getAudioDuration(audio_path_concaded)

                for index in range(len(audio_paths)):
                    print(f'{index + 1}_converted: {RacoonMediaTools.getAudioDuration(audio_paths[index])}')

                for index in range(len(oryginal_durations)):
                    print(f'{index + 1}: {oryginal_durations[index]}')

                print(f'Oryginal duration: {converted_duration}')
                print(f'Converted duration: {final_duration}')
                print(f'Duration difference (converted - oryginal): {RacoonMediaTools.parse_time_string(final_duration) - RacoonMediaTools.parse_time_string(converted_duration)}')

                
        concad_audio(self.sound_input_paths)

