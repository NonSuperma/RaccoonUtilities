from colorama import init, Fore, Back, Style
from Raccoon import audioUtilities as audio
from Raccoon import miscUtilities, mediaUtilities, windowsUtilities
from Raccoon import errors as RErrors
from playsound3 import playsound
from pathlib import Path
import subprocess as sp
import sys
import os


def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return Path.joinpath(base_path, relative_path)


def play_success_sound() -> None:
    sound_file = resource_path('SourceFiles/au5-1.mp3')
    playsound(sound_file)


def make_video(self, output_path: Optional[Path] = None, lenght_check: bool = False, pure_audio: bool = False):
    init(autoreset=True)

    if output_path is None:
        output_path = self.sound_input_paths[0].parent

    if len(self.sound_input_paths) == 1:
        sound_input_path: Path = self.sound_input_paths[0]
        name = sound_input_path.stem

        duration = RaccoonMediaTools.get_audio_duration(sound_input_path)
        if pure_audio:
            ffmpegOutput = sp.run(f'ffmpeg '
                                  f'-loglevel fatal '
                                  f'-y '
                                  f'-loop 1 '
                                  f'-framerate 1 '
                                  f'-i "{self.image_input_path}" '
                                  f'-i "{sound_input_path}" '
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
                                  f''
                                  f'-y '
                                  f'-loop 1 '
                                  f'-framerate 1 '
                                  f'-i "{self.image_input_path}" '
                                  f'-i "{sound_input_path}" '
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
            oryginalDuration = RaccoonMediaTools.get_audio_duration(sound_input_path)
            converterDuration = RaccoonMediaTools.get_audio_duration(Path(f'{output_path}\\{name}.mp4'))
            if oryginalDuration != converterDuration:
                temp_path = sound_input_path.stem + "_temp" + sound_input_path.suffix
                sp.run(
                    f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_path}" -c copy "{temp_path}"',
                    shell=True)
                os.replace(temp_path, sound_input_path)
        return ffmpegOutput

    else:
        paths_to_file_no_extension = []
        for INDEX in range(0, len(self.sound_input_paths)):
            paths_to_file_no_extension.append(self.sound_input_paths[INDEX].stem)

        for INDEX in range(len(paths_to_file_no_extension)):
            ffmpegOutput = []
            ffmpegOutputPart = sp.run(
                f'ffmpeg '
                f'-y '
                f'-loglevel warning '
                f'-loop 1 '
                f'-i "{self.image_input_path}" '
                f'-i "{self.sound_input_paths[INDEX]}" '
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
                oryginalDuration = RaccoonMediaTools.get_audio_duration(sound_input_path[INDEX])
                converterDuration = RaccoonMediaTools.get_audio_duration(
                    Path.joinpath(output_path, paths_to_file_no_extension[INDEX]).with_suffix('.mp4'))

                if oryginalDuration != converterDuration:
                    temp_path = sound_input_path[INDEX].stem + "_temp" + sound_input_path[INDEX].suffix
                    sp.run(
                        f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_path[INDEX]}" -c copy "{temp_path}"',
                        shell=True)
                    os.replace(temp_path, sound_input_path[INDEX])
                ffmpegOutput.append(ffmpegOutputPart)

        return ffmpegOutput


def make_album(self, final_filename: str, output_path: Optional[Path] or None = None):
    init(autoreset=True)
    TEST = False

    if output_path is None:
        output_path = self.sound_input_paths[0].parent
        if TEST:
            print(output_path)

    def concad_audio(audio_paths: list[Path]):
        convertion_sufix = '.flac'
        final_concad_file_path = Path.joinpath(output_path, final_filename).with_suffix(convertion_sufix)
        final_mp4_file_path = Path(f'{output_path}\\{final_filename}.mp4')

        # check for uneven image input dimentions and scale if yes
        print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
              f'Checking {Fore.LIGHTYELLOW_EX}"{self.image_input_path.name}"{Fore.RESET} '
              f'for uneven image dimentions...')
        oryginal_dimentions = mediaUtilities.get_media_dimentions(self.image_input_path)
        try:
            ffmpegOutput = RaccoonMediaTools.check_scale_to_even_dimentions(self.image_input_path)
            if ffmpegOutput[0] == 1:
                print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
                      f'Scaled {Fore.LIGHTYELLOW_EX}"{self.image_input_path.name}"{Fore.RESET} '
                      f'from ({oryginal_dimentions[0]}:{oryginal_dimentions[1]}) '
                      f'to even '
                      f'({ffmpegOutput[1][0]}:{ffmpegOutput[1][1]}) '
                      f'dimentions!\n')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
                      f'{Fore.LIGHTGREEN_EX}Dimentions are even!\n{Style.RESET_ALL}')
        except RaccoonErrors.FfmpegGeneralError:
            RaccoonMediaTools.ask_exit(f'{Fore.RED}Something went wrong while scaling the cover image!{Fore.RESET}\n'
                                       f'Ffmpeg needs even dimentions to work\n'
                                       f'Try manually changing the dimentions to be even and then try again')

        # Temp audio paths like output_path//"audio1.flac"
        temp_audio_paths = []
        for index in range(len(audio_paths)):
            temp_audio_paths.append(Path(output_path, 'audio' + str(index)).with_suffix(convertion_sufix))

        # Test to see input paths, oryginal added durations and temp audio paths
        if TEST:
            for audio_path in audio_paths:
                print(audio_path)

        # Convert every audio input to the temp audio file
        for index in range(len(audio_paths)):
            audio_path = audio_paths[index]
            temp_audio_path = temp_audio_paths[index]

            print(f'{Fore.LIGHTCYAN_EX}[Converter]{Style.RESET_ALL} '
                  f'Converting {Fore.LIGHTYELLOW_EX}"{audio_path.name}"{Fore.RESET} '
                  f'to {convertion_sufix}...  '
                  f'{Fore.LIGHTGREEN_EX}({index + 1}/{len(audio_paths)}){Fore.RESET}')
            try:
                ffmpegOutput_converter = sp.run(f'ffmpeg '
                                                f'-loglevel fatal '
                                                f'-y '
                                                f'-i "{audio_path}" '
                                                f'-c:a flac '
                                                f'"{temp_audio_path}"',
                                                shell=True, capture_output=False)
                if ffmpegOutput_converter.returncode != 0:
                    raise RaccoonErrors.FfmpegGeneralError('Something went to shit')
            except RaccoonErrors.FfmpegGeneralError:
                RaccoonMediaTools.ask_exit("Something went wrong while converting audio input into flac")
        try:
            with open(output_path / 'audio_input_list.txt', 'w+', encoding='utf-8') as audio_input_list:
                for temp_audio_path in temp_audio_paths:
                    audio_input_list.write(f"file '{str(temp_audio_path)}'\n")
        except (Exception,):
            RaccoonMediaTools.ask_exit(
                f'{Fore.RED}Something went wrong while creating and writing the audio list!{Fore.RES}\n')

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
                                         f'"{final_concad_file_path}"',
                                         capture_output=True)
            if ffmpegOutput_concad.returncode != 0:
                raise RaccoonErrors.FfmpegConcadError('something went to shit')

        except RaccoonErrors.FfmpegConcadError:
            print(ffmpegOutput_concad)
            RaccoonMediaTools.ask_exit(f'{Fore.LIGHTCYAN_EX}[Concad]{Style.RESET_ALL} '
                                       f'{Fore.RED}Something went wrong while concading!{Style.RESET_ALL}')
        else:
            print(f'{Fore.LIGHTCYAN_EX}[Concad]{Fore.RESET} '
                  f'{Fore.GREEN}Done!{Fore.RESET} ')

        # Get times

        # Duration list BEFORE CONVERTION
        try:
            oryginal_audios_durations = []
            for audio_path in audio_paths:
                oryginal_audios_durations.append(RaccoonMediaTools.get_audio_duration(audio_path))
            oryginal_audios_duration = RaccoonMediaTools.add_times(oryginal_audios_durations)
        except (Exception,):
            print(f'\n{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Pre concad added files duration: '
                  f'{Fore.RED}ERROR{Fore.RESET}')
        else:
            print(f'\n{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Pre concad added files duration: '
                  f'{Fore.LIGHTYELLOW_EX}{oryginal_audios_duration}{Fore.RESET}')

        # Duration list AFTER converting to flac
        try:
            converted_durations = []
            for path in temp_audio_paths:
                converted_durations.append(RaccoonMediaTools.get_audio_duration(path))

            converted_duration = RaccoonMediaTools.add_times(converted_durations)

        except (Exception,):
            print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Post concad added files duration: '
                  f'{Fore.RED}ERROR{Fore.RESET}')
        else:
            print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Post concad added files duration: '
                  f'{Fore.LIGHTYELLOW_EX}{converted_duration}{Fore.RESET}')

        # Duration of the output .flac file
        try:
            final_flac_duration = RaccoonMediaTools.get_audio_duration(final_concad_file_path)
        except (Exception,):
            print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Final file duration: '
                  f'{Fore.RED}ERROR{Fore.RESET}')
        else:
            print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Final file duration: '
                  f'{Fore.LIGHTYELLOW_EX}{final_flac_duration}{Fore.RESET}')

        try:
            convertionDifference = RaccoonMediaTools.hhmmss_to_seconds(
                final_flac_duration) - RaccoonMediaTools.hhmmss_to_seconds(oryginal_audios_duration)
        except (Exception,):
            print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                  f'Duration difference (converted - oryginal): '
                  f'{Fore.RED}ERROR{Fore.RESET}')
        else:
            if 1.000 > convertionDifference > -1.000:
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                      f'Duration difference (converted - oryginal): '
                      f'{Fore.LIGHTGREEN_EX}{RaccoonMediaTools.seconds_to_hhmmss(convertionDifference)}{Fore.RESET}')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Time counter]{Fore.RESET} '
                      f'Duration difference (converted - oryginal): '
                      f'{Fore.RED}{RaccoonMediaTools.seconds_to_hhmmss(convertionDifference)}{Fore.RESET}')

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
                                      f'-i "{final_concad_file_path}" '
                                      f'-c:v libx264 '
                                      f'-tune stillimage '
                                      f'-c:a mp3 '
                                      f'-b:a 320k '
                                      f'-t {converted_duration} '
                                      f'-movflags +faststart '
                                      f'-vf "format=yuv420p" '
                                      f'-r 1 '
                                      f'"{final_mp4_file_path}"',
                                      shell=True, capture_output=False)
            if ffmpegOutput_vid.returncode != 0:
                raise RaccoonErrors.FfmpegGeneralError('something went to shit')

        except RaccoonErrors.FfmpegGeneralError:
            print(
                f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Style.RESET_ALL} {Fore.RED}Something went wrong while making the video!{Style.RESET_ALL}')
            print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Style.RESET_ALL} Trying without re-encoding the audio...')
            try:
                ffmpegOutput_vid = sp.run(f'ffmpeg '
                                          f'-loglevel fatal '
                                          f'-y '
                                          f'-loop 1 '
                                          f'-framerate 1 '
                                          f'-i "{self.image_input_path}" '
                                          f'-i "{final_concad_file_path}" '
                                          f'-c:v libx264 '
                                          f'-tune stillimage '
                                          f'-c:a copy '
                                          f'-t {converted_duration} '
                                          f'-movflags +faststart '
                                          f'-vf "format=yuv420p" '
                                          f'-r 1 '
                                          f'"{ofinal_mp4_file_path}"',
                                          shell=True, capture_output=False)
                if ffmpegOutput_vid.returncode != 0:
                    raise RaccoonErrors.FfmpegGeneralError('something went to shit')
            except RaccoonErrors.FfmpegGeneralError:
                RaccoonMediaTools.ask_exit(f'Yeah something went to *shit shit* while creating the final video\n'
                                           f'Maybe try  again?')
            else:
                print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Fore.RESET} '
                      f'{Fore.GREEN}Done!{Fore.RESET}')
        else:
            print(f'{Fore.LIGHTCYAN_EX}[Vid Maker]{Fore.RESET} '
                  f'{Fore.GREEN}Done!{Fore.RESET}')

    concad_audio(self.sound_input_paths)


def main():
    init(autoreset=True)

    test = False
    if test:
        imageInputPath = Path('Test_Source\\clipboard__square.png')
    else:
        try:
            imageInputPath = Ru.win_file_path('Pick the album cover image', filetypes='image')
        except RuE.MissingInputError:
            Ru.ask_exit("User closed the window")

    if test:
        soundInputPaths = [file for file in p.rglob("*.webp")]
    else:
        try:
            selection = [
                ("All without images", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus *.webm *.mp4 *.mov *.avi *.wmv"),
                ("MP3 files", "*.MP3"),
                ("AAC files", "*.AAC"),
                ("FLAC files", "*.FLAC"),
                ("WAV files", "*.WAV"),
                ("PCM files", "*.PCM"),
                ("M4A files", "*.M4A"),
                ("OPUS files", "*.opus"),
                ("Video files", "*.webm *.mp4 *.mov *.avi *.wmv")
            ]
            soundInputPaths = Ru.win_files_path('Pick songs', filetypes=selection)
        except RuE.MissingInputError:
            Ru.ask_exit("User closed the window")

    workingFolderPath = soundInputPaths[0].parent
    workingFolderName = workingFolderPath.name

    if test:
        albumName = 'TEST'
    else:
        userChoice = input(
            f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} The selected songs are in a folder called {Fore.GREEN}{workingFolderName}{Fore.RESET}\n'
            f'       Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n'
            f'       {Fore.LIGHTBLUE_EX}[]{Fore.RESET} gets converted into {Fore.GREEN}{workingFolderName}{Fore.RESET}\n'
            f'       {Fore.LIGHTBLUE_EX}--full{Fore.RESET} removes {Fore.LIGHTBLUE_EX}[Full Album]{Fore.RESET} from the final name\n'
            f'       : '
        )

        if userChoice == '':
            albumName = workingFolderName + ' [Full Album]'
        elif userChoice == '--full':
            albumName = workingFolderName

        else:
            albumName = userChoice

            if '[]' in albumName:
                albumName = albumName.replace('[]', workingFolderName)

            if '--full' in albumName:
                albumName = albumName.replace('--full', '')
                if '  ' in albumName:
                    albumName = albumName.replace('  ', ' ')
            else:
                albumName += ' [Full Album]'

    print(f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} Filename chosen: {Fore.LIGHTBLUE_EX}"{albumName}"{Fore.RESET}\n')

    album = Ru(imageInputPath, soundInputPaths)
    album.make_album(albumName)


if __name__ == "__main__":
    main()
    sys.exit(0)
