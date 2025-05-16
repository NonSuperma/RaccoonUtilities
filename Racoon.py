import subprocess as sp
from tkinter import filedialog, Tk, BooleanVar
from typing import Optional, List
from colorama import init, Fore, Back, Style
from datetime import datetime, timedelta
from typing import Optional, Sequence, Tuple, List, Union, cast
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

    class FfmpegGeneralError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    class FfmpegConcadError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)


class RacoonMediaTools:

    def __init__(self, image_input_path: Path, sound_input_paths: list[Path]) -> None:
        self.image_input_path: Path = image_input_path
        self.sound_input_paths: list[Path] = sound_input_paths

    @staticmethod
    def seconds_to_hhmmss(s: float) -> str:
        sign = "-" if s < 0 else ""
        s = abs(s)
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = s % 60
        return f"{sign}{h:02d}:{m:02d}:{sec:06.3f}"

    @staticmethod
    def hhmmss_to_seconds(timestamp: str) -> float:
        parts = timestamp.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid format: expected 'HH:MM:SS.sss', got '{timestamp}'")

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds


    @staticmethod
    def add_times(time_list: list[str]) -> str:
        total = 0
        for t in time_list:
            total += RacoonMediaTools.hhmmss_to_seconds(t)
        return RacoonMediaTools.seconds_to_hhmmss(total)

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
    def winFilePath(message: str, filetypes=None) -> Path:
        root = Tk()
        root.lift()
        root.withdraw()

        kwargs = {"title": message, "parent": root}
        if filetypes is not None:
            if filetypes == 'audio':
                selection = cast(Sequence[Tuple[str, str]],
                                 [
                                    ("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
                                    ("MP3 files",   "*.MP3"),
                                    ("AAC files",   "*.AAC"),
                                    ("FLAC files",  "*.FLAC"),
                                    ("WAV files",   "*.WAV"),
                                    ("PCM files",   "*.PCM"),
                                    ("M4A files",   "*.M4A"),
                                    ("OPUS files",  "*.opus"),
                                 ])
                kwargs["filetypes"] = selection
            elif filetypes == 'image':
                selection = cast(Sequence[Tuple[str, str]],
                                 [
                                    ("Image files", "*.PNG *.JPEG *.jpg"),
                                    ("PNG files",   "*.PNG"),
                                    ("JPEG files",   "*.JPEG"),
                                    ("JPG files", "*.jpg")
                                 ])
                kwargs["filetypes"] = selection
            else:
                kwargs["filetypes"] = filetypes

        file_path_str = filedialog.askopenfilename(**kwargs)
        file_path = Path(file_path_str)

        if not file_path_str:
            raise RacoonErrors.MissingInputError('User closed the window')

        return file_path

    @staticmethod
    def winFilesPath(message: str, filetypes=None) -> list[Path]:
        root = Tk()
        root.lift()
        root.withdraw()
        kwargs = {"title": message, "parent": root}
        if filetypes is not None:
            if filetypes == 'audio':
                selection = cast(Sequence[Tuple[str, str]],
                                 [
                                    ("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
                                    ("MP3 files",   "*.MP3"),
                                    ("AAC files",   "*.AAC"),
                                    ("FLAC files",  "*.FLAC"),
                                    ("WAV files",   "*.WAV"),
                                    ("PCM files",   "*.PCM"),
                                    ("M4A files",   "*.M4A"),
                                    ("OPUS files",  "*.opus"),
                                 ])
                kwargs["filetypes"] = selection
            elif filetypes == 'image':
                selection = cast(Sequence[Tuple[str, str]],
                                 [
                                    ("Image files", "*.PNG *.JPEG"),
                                    ("PNG files",   "*.PNG"),
                                    ("JPEG files",   "*.JPEG")
                                 ])
                kwargs["filetypes"] = selection
            else:
                kwargs["filetypes"] = filetypes

        file_paths = root.tk.splitlist(
            filedialog.askopenfilenames(**kwargs)
        )
        root.destroy()

        if not file_paths:
            raise RacoonErrors.MissingInputError("User closed the window")

        return [Path(p) for p in file_paths]

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
    def getAudioDuration(file_path: Path) -> str or None:

        ffprobeOutput = sp.run(
            f'ffprobe '
            f'-show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 '
            f'"{file_path}"',
            shell=True, capture_output=True)

        if ffprobeOutput.returncode != 0:
            print(ffprobeOutput.stdout.decode())
            return None

        else:
            return RacoonMediaTools.seconds_to_hhmmss(float(ffprobeOutput.stdout.decode()))

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
                    f'-c:a aac '
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
        TEST = True

        if output_path is None:
            output_path = self.sound_input_paths[0].parent
            if TEST:
                print(output_path)

        def concad_audio(audio_paths: list[Path]):
            convertion_sufix = '.flac'
            final_concad_file_path = Path.joinpath(output_path, final_filename).with_suffix(convertion_sufix)

            # Temp audio paths like output_path//"audio1.flac"
            temp_audio_paths = []
            for index in range(len(audio_paths)):
                temp_audio_paths.append(Path(output_path, 'audio' + str(index)).with_suffix(convertion_sufix))

            # Test to see input paths, oryginal added durations and temp audio paths
            if TEST:
                for audio_path in audio_paths:
                    print(audio_path)


            #Convert every audio input to the temp audio file
            for index in range(len(audio_paths)):
                audio_path = audio_paths[index]
                temp_audio_path = temp_audio_paths[index]

                print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
                      f'Converting {Fore.LIGHTYELLOW_EX}"{audio_path.name}"{Fore.RESET} '
                      f'to {convertion_sufix}...  '
                      f'{Fore.LIGHTGREEN_EX}({index+1}/{len(audio_paths)}){Fore.RESET}')

                ffmpegOutput_converter = sp.run(f'ffmpeg '
                                                f'-loglevel fatal '
                                                f'-y '
                                                f'-i "{audio_path}" '
                                                f'-c:a flac '
                                                f'"{temp_audio_path}"',
                                                shell=True, capture_output=False)

            try:
                with open(output_path / 'audio_input_list.txt', 'w+', encoding='utf-8') as audio_input_list:
                    for temp_audio_path in temp_audio_paths:
                        audio_input_list.write(f"file '{str(temp_audio_path)}'\n")
            except (Exception,):
                RacoonMediaTools.askExit(f'{Fore.RED}Something went wrong while creating and writing the audio list!{Fore.RES}\n')

            # Concad audio files
            print(f'\n{Fore.LIGHTCYAN_EX}[Concad]{Style.RESET_ALL} Concading audio files into one...  ')
            try:
                ffmpegOutput_concad = sp.run(f'ffmpeg '
                                             f'-y '
                                             f'-loglevel fatal '
                                             f'-f concat '
                                             f'-safe 0 '
                                             f'-i "{Path.joinpath(output_path, 'audio_input_list.txt')}" '
                                             f'-c:a flac '
                                             f'"{final_concad_file_path}"'
                                             , capture_output=True)
                if ffmpegOutput_concad.returncode != 0:
                    raise RacoonErrors.FfmpegConcadError('something went to shit')

            except RacoonErrors.FfmpegConcadError:
                print(ffmpegOutput_concad)
                RacoonMediaTools.askExit(f'{Fore.LIGHTCYAN_EX}[Concad]{Style.RESET_ALL} {Fore.RED}Something went wrong while concading!{Style.RESET_ALL}')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Concad]{Fore.RESET} {Fore.GREEN}Done!{Fore.RESET} ')

            # Get times

            # Duration list BEFORE CONVERTION
            try:
                oryginal_audios_durations = []
                for audio_path in audio_paths:
                    oryginal_audios_durations.append(RacoonMediaTools.getAudioDuration(audio_path))
                oryginal_audios_duration = RacoonMediaTools.add_times(oryginal_audios_durations)
            except (Exception,):
                print(f'\n{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Pre concad added files duration: {Fore.RED}ERROR{Fore.RESET}')
            else:
                print(f'\n{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Pre concad added files duration: {oryginal_audios_duration}')
            # Duration list after converting to flac
            try:
                converted_durations = []
                for path in temp_audio_paths:
                    converted_durations.append(RacoonMediaTools.getAudioDuration(path))

                converted_duration = RacoonMediaTools.add_times(converted_durations)

            except (Exception,):
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Post concad added files duration: {Fore.RED}ERROR{Fore.RESET}')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Post concad added files duration: {converted_duration}')

            # Duration of the output file
            try:
                final_duration = RacoonMediaTools.getAudioDuration(final_concad_file_path)
            except (Exception,):
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Final file duration: {Fore.RED}ERROR{Fore.RESET}')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Final file duration: {final_duration}')

            try:
                convertionDifference = RacoonMediaTools.seconds_to_hhmmss(RacoonMediaTools.hhmmss_to_seconds(final_duration) - RacoonMediaTools.hhmmss_to_seconds(oryginal_audios_duration))
            except (Exception,):
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Duration difference (converted - oryginal): {Fore.RED}ERROR{Fore.RESET}')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} Duration difference (converted - oryginal): {convertionDifference}')


            # Remove temp audio files from disc
            if not TEST:
                Path.joinpath(output_path, 'audio_input_list.txt').unlink()
                for path in temp_audio_paths:
                    path.unlink()


            # Make the final .mp4 video
            print(f'\n{Fore.LIGHTCYAN_EX}[Vid Maker]{Style.RESET_ALL} Making video...')
            try:
                ffmpegOutput_vid = sp.run(f'ffmpeg '
                                          f'-loglevel fatal '
                                          f'-y '
                                          f'-loop 1 '
                                          f'-framerate 1 '
                                          f'-i "{self.image_input_path}" '
                                          f'-i "{output_path}\\{final_filename}.flac" '
                                          f'-c:v libx264 '
                                          f'-tune stillimage '
                                          f'-c:a aac '
                                          f'-b:a 128k '
                                          f'-t {converted_duration} '
                                          f'-movflags +faststart '
                                          f'-vf "format=yuv420p" '
                                          f'-r 1 '
                                          f'"{output_path}\\{final_filename}.mp4"',
                                          shell=True, capture_output=False)
                if ffmpegOutput_vid.returncode != 0:
                    raise RacoonErrors.FfmpegGeneralError('something went to shit')

            except RacoonErrors.FfmpegGeneralError:
                print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Style.RESET_ALL} {Fore.RED}Something went wrong while making the video!{Style.RESET_ALL}')
                print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Style.RESET_ALL} Trying without re-encoding the audio...')
                try:
                    ffmpegOutput_vid = sp.run(f'ffmpeg '
                                              f'-loglevel fatal '
                                              f'-y '
                                              f'-loop 1 '
                                              f'-framerate 1 '
                                              f'-i "{self.image_input_path}" '
                                              f'-i "{output_path}\\{final_filename}.flac" '
                                              f'-c:v libx264 '
                                              f'-tune stillimage '
                                              f'-c:a copy '
                                              f'-t {converted_duration} '
                                              f'-movflags +faststart '
                                              f'-vf "format=yuv420p" '
                                              f'-r 1 '
                                              f'"{output_path}\\{final_filename}.mp4"',
                                              shell=True, capture_output=False)
                    if ffmpegOutput_vid.returncode != 0:
                        raise RacoonErrors.FfmpegGeneralError('something went to shit')
                except RacoonErrors.FfmpegGeneralError:
                    RacoonMediaTools.askExit(f'Yeah something went to *shit shit* while creating the final video\n'
                                             f'Maybe try  again?')
                else:
                    print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Fore.RESET} {Fore.GREEN}Done!{Fore.RESET} ')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Fore.RESET} {Fore.GREEN}Done!{Fore.RESET} ')




        concad_audio(self.sound_input_paths)

