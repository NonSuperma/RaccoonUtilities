from setuptools.command.bdist_egg import can_scan

from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.windowsUtilities import *
from colorama import Fore, Back, Style
import subprocess
import sys
import shutil
import json
from pathlib import Path

INFO = f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET}'
INPUT = f'{Fore.LIGHTCYAN_EX}[Input]{Fore.RESET}'
mvb_clrln = '\r\033[2K'


def ask_bitrate() -> int:
    while True:
        print(f'{INPUT} Choose the desired bitrate ["k" converts to thousants -> 320k = 320000]')
        userChoice = input(f'{INPUT}: ').strip().lower()

        if 'k' in userChoice:
            clean_choice = userChoice.replace('k', '').strip()
            if clean_choice.isdigit():
                return int(clean_choice) * 1000

        if userChoice.isdigit():
            return int(userChoice)

        print(f'{Fore.RED}'
              f'Invalid input. Please enter a valid number (e.g., 320000 or 320k).'
              f'{Fore.RESET}')


def has_video_stream(file_path: Path) -> bool:
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_type',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return 'video' in result.stdout


def ask_album_name(folder_name: str) -> str:
    user_choice = input(
        f'{INFO} The selected songs are in a folder called {Fore.LIGHTMAGENTA_EX}{folder_name}{Fore.RESET}\n'
        f'       Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n'
        f'       {Fore.LIGHTBLUE_EX}[]{Fore.RESET} gets converted into {Fore.LIGHTMAGENTA_EX}{folder_name}{Fore.RESET}\n'
        f'       {Fore.LIGHTBLUE_EX}--full{Fore.RESET} removes {Fore.LIGHTBLUE_EX}[Full Album]{Fore.RESET} from the final name\n'
        f'{INPUT}: '
    )

    if not user_choice:
        return f"{folder_name} [Full Album]"

    if user_choice == '--full':
        return folder_name

    album_name = user_choice.replace('[]', folder_name)

    if '--full' in album_name:
        album_name = album_name.replace('--full', '').strip()
    else:
        album_name = f"{album_name} [Full Album]"

    return album_name


def main():
    choices_description = (
        f'{Fore.LIGHTCYAN_EX}'
        '-----------------------------------------------------------------------------------------------------------'
        f'{Fore.RESET}\n'
        '   1 - Album to mp4 - Create an mp4 file from multiple audio files and optionally a cover image\n'
        '   2 - Tracks to mp4 - Create seperate mp4 file from multiple or one flac files and optionally a cover image\n'
        '   3 - Mp3 - Create an mp3 file from any losless audio file\n'
        f'{Fore.LIGHTCYAN_EX}'
        '-----------------------------------------------------------------------------------------------------------'
        f'{Fore.RESET}')

    print(choices_description)
    userChoice = input(f'{INPUT}: ')
    console_clear_n(choices_description.count('\n') + 2)

    match userChoice:
        case '1':  # Album to mp4
            track_paths = win_files_path('Tracks', 'audio')
            folder_path = track_paths[0].parent
            temp_folder_path = folder_path / 'temp'
            temp_folder_path.mkdir(exist_ok=True)

            tracks_data = []
            for track_path in track_paths:
                tracks_data.append(get_media_file_data(track_path))

            format_names = []
            for track_data in tracks_data:
                format_names.append(track_data['format']['format_name'])
            format_names = list(set(format_names))

            if all(has_video_stream(path) for path in track_paths):
                first_track_data = tracks_data[0]
                print(f'{INFO}Embedded cover image found in all audio files!\n'
                      f'{Fore.LIGHTMAGENTA_EX}'
                      f'First track\'s album cover\'s info:\n'
                      f'------------------------------\n'
                      f'Resolution: {first_track_data['video'][0]['width']}x{first_track_data['video'][0]['height']}\n'
                      f'Codec name: {first_track_data['video'][0]['codec_name']}\n'
                      f'------------------------------'
                      f'{Fore.RESET}')
                print(f'{INPUT}Use embedded image as cover going forward? y/n\n'
                      f'       ("No" will let you choose the cover file manually)')
                userChoice = input(f'{INPUT}:').strip().lower()


                cover_path = None
                cover_extracted = False
                if userChoice == 'y':
                    cover_extracted = True
                    cover_filename = 'cover_extracted.png'
                    cover_path = Path.joinpath(temp_folder_path, cover_filename)

                    cmd = [
                        'ffmpeg', '-nostdin',
                        '-y',
                        '-v', 'error',
                        '-i', str(track_paths[0]),
                        '-map', '0:v:0',
                        '-frames:v', '1',
                        '-update', '1',
                        str(cover_path)
                    ]
                    try:
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"{Fore.RED}Error running ffmpeg:{Style.RESET_ALL}\n{e.stderr}")
                        print(f'Choose cover manually')
                        cover_path = win_file_path('Cover', 'image')
                else:
                    cover_path = win_file_path('Cover', 'image')
            else:
                cover_path = win_file_path('Cover', 'image')

            cover_filename = cover_path.name

            if len(format_names) > 1:
                print(f'{INFO} Mixed formats -> MP4')
            else:
                format_name = format_names[0]
                match format_name:
                    case 'flac':
                        print(f'{INFO} FLAC -> MP4')

                        folder_name = folder_path.name
                        album_name = ask_album_name(folder_name)

                        print(f'{INFO} Album filename chosen: {Fore.LIGHTBLUE_EX}"{album_name}"{Fore.RESET}\n')

                        ffmpeg_track_list_file_path = Path.joinpath(temp_folder_path, 'file_list.txt')

                        with open(ffmpeg_track_list_file_path, 'w+', encoding='utf-8') as file:
                            for track_path in track_paths:
                                file.write(f"file '{str(track_path.as_posix())}'\n")

                        chosen_bitrate = ask_bitrate()

                        mp4_output_path = folder_path / (album_name + '.mp4')

                        cmd = ['ffmpeg', '-y', '-nostdin',
                               '-loglevel', 'fatal',
                               '-loop', '1',
                               '-framerate', '1',
                               '-i', str(cover_path),
                               '-f', 'concat',
                               '-safe', '0',
                               '-i', str(ffmpeg_track_list_file_path),
                               '-c:v', 'libx264',
                               '-tune', 'stillimage',
                               '-c:a', 'libmp3lame',
                               '-b:a', str(chosen_bitrate),
                               '-pix_fmt', 'yuv420p',
                               '-shortest',
                               '-movflags', '+faststart',
                               str(mp4_output_path)]

                        print(f'{Fore.LIGHTYELLOW_EX}Encoding...{Fore.RESET}', end='', flush=True)
                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=False,
                                text=True,
                                check=True
                            )
                        except subprocess.CalledProcessError as e:
                            ask_exit(f"{Fore.RED}Error running ffmpeg:{Style.RESET_ALL}\n{e.stderr}", 30)
                        finally:
                            print(f'{mvb_clrln}{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}\n')

                        shutil.rmtree(temp_folder_path)
                    case 'mp3':
                        print(f'\n{Fore.LIGHTGREEN_EX}MP3 -> MP4{Fore.RESET}')

                    case 'ogg':
                        print(f'{Fore.LIGHTGREEN_EX}OGG -> MP4{Fore.RESET}')
                    case _:
                        print(
                            f'{Fore.LIGHTYELLOW_EX}[Warning] Unaccounted audio file format. May produce unexpected results\n'
                            f'(Be sure to understand lossy conversion){Fore.RESET}')

        case '2':  # Tracks to mp4
            track_paths = win_files_path('Tracks', 'audio')
            folder_path = track_paths[0].parent
            temp_folder_path = folder_path / 'temp'
            temp_folder_path.mkdir(exist_ok=True)

            tracks_data = []
            for track_path in track_paths:
                tracks_data.append(get_media_file_data(track_path))

            format_names = []
            for track_data in tracks_data:
                format_names.append(track_data['format']['format_name'])
            format_names = list(set(format_names))

            if all(has_video_stream(path) for path in track_paths):
                first_track_data = tracks_data[0]
                print(f'{INFO}Embedded cover image found in all audio files!\n'
                      f'{Fore.LIGHTMAGENTA_EX}'
                      f'First track\'s album cover\'s info:\n'
                      f'------------------------------\n'
                      f'Resolution: {first_track_data['video'][0]['width']}x{first_track_data['video'][0]['height']}\n'
                      f'Codec name: {first_track_data['video'][0]['codec_name']}\n'
                      f'------------------------------'
                      f'{Fore.RESET}')
                print(f'{INPUT}Use embedded image as cover going forward? y/n\n'
                      f'       ("No" will let you choose the cover file manually)')
                userChoice = input(f'{INPUT}:').strip().lower()


                cover_path = None
                cover_extracted = False
                if userChoice == 'y':
                    cover_extracted = True
                    cover_filename = 'cover_extracted.png'
                    cover_path = Path.joinpath(temp_folder_path, cover_filename)

                    cmd = [
                        'ffmpeg', '-nostdin',
                        '-y',
                        '-v', 'error',
                        '-i', str(track_paths[0]),
                        '-map', '0:v:0',
                        '-frames:v', '1',
                        '-update', '1',
                        str(cover_path)
                    ]
                    try:
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"{Fore.RED}Error running ffmpeg:{Style.RESET_ALL}\n{e.stderr}")
                        print(f'Choose cover manually')
                        cover_path = win_file_path('Cover', 'image')
                else:
                    cover_path = win_file_path('Cover', 'image')
            else:
                cover_path = win_file_path('Cover', 'image')

            cover_filename = cover_path.name

            if len(format_names) > 1:
                ...
            else:
                match format_names[0]:
                    case 'flac':

                        chosen_bitrate = ask_bitrate()

                        for index, track_path in enumerate(track_paths, start=1):
                            mp4_folder_output_path = folder_path / 'mp4'
                            mp4_folder_output_path.mkdir(exist_ok=True)

                            mp4_output_path = mp4_folder_output_path / track_path.with_suffix('.mp4').name

                            cmd = ['ffmpeg', '-y', '-nostdin',
                                   '-loglevel', 'fatal',
                                   '-loop', '1',
                                   '-framerate', '1',
                                   '-i', str(cover_path),
                                   '-i', str(track_path),
                                   '-c:v', 'libx264',
                                   '-tune', 'stillimage',
                                   '-c:a', 'libmp3lame',
                                   '-b:a', str(chosen_bitrate),
                                   '-pix_fmt', 'yuv420p',
                                   '-shortest',
                                   '-movflags', '+faststart',
                                   str(mp4_output_path)]

                            print(f'{mvb_clrln}{Fore.LIGHTYELLOW_EX}Encoding... ({index}/{len(track_paths)})', end='',
                                  flush=True)
                            try:
                                subprocess.run(cmd, check=True, capture_output=True, text=True)
                            except subprocess.CalledProcessError as e:
                                ask_exit(f'{Fore.RED}Error running ffmpeg!{Fore.RED}:\n'
                                         f'{e.stderr}', 30)
                    case 'mp3':
                        bitrate_avg = 0
                        for track_data in tracks_data:
                            bitrate_avg +=track_data['audio'][0]['bit_rate']
                        bitrate_avg /= len(track_paths)

                        for index, track_path in enumerate(track_paths, start=1):
                            mp4_folder_output_path = folder_path / 'mp4'
                            mp4_folder_output_path.mkdir(exist_ok=True)

                            mp4_output_path = mp4_folder_output_path / track_path.with_suffix('.mp4').name

                            cmd = ['ffmpeg', '-y', '-nostdin',
                                   '-loglevel', 'fatal',
                                   '-loop', '1',
                                   '-framerate', '1',
                                   '-i', str(cover_path),
                                   '-i', str(track_path),
                                   '-c:v', 'libx264',
                                   '-tune', 'stillimage',
                                   '-c:a', 'copy',
                                   '-pix_fmt', 'yuv420p',
                                   '-shortest',
                                   '-movflags', '+faststart',
                                   str(mp4_output_path)]

                            print(f'{mvb_clrln}{Fore.LIGHTYELLOW_EX}Encoding... ({index}/{len(track_paths)})', end='',
                                  flush=True)
                            try:
                                subprocess.run(cmd, check=True, text=True, capture_output=True)
                            except subprocess.CalledProcessError as e:
                                ask_exit(f'\n\n{Fore.RED}Error running ffmpeg!{Fore.RESET}:\n'
                                         f'{e.stderr}', 30)
                    case '_':
                        ...

            shutil.rmtree(temp_folder_path)
            ask_exit(f'{mvb_clrln}{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}')

        case '3':  # Mp3
            try:
                track_paths = win_files_path('Tracks', 'audio')
            except MissingInputError:
                ask_exit(f'{Fore.LIGHTRED_EX}User closed the window{Fore.RESET}', timeout=10)

            folder_path = track_paths[0].parent

            tracks_data = [get_media_file_data(track_path) for track_path in track_paths]

            format_names = list(set([track_data['format']['format_name'] for track_data in tracks_data]))

            if len(format_names) > 1:
                ...
            else:
                match format_names[0]:
                    case 'flac':
                        chosen_bitrate = ask_bitrate()

                        for index, track_path in enumerate(track_paths, start=1):
                            mp3_output_folder_path = folder_path / 'mp3'
                            mp3_output_folder_path.mkdir(exist_ok=True)

                            mp3_output_path = mp3_output_folder_path / track_path.with_suffix('.mp3').name

                            cmd = ['ffmpeg', '-y', '-nostdin',
                                   '-loglevel', 'fatal',
                                   '-i', track_path,
                                   '-map_metadata', '0',
                                   '-c:a', 'libmp3lame',
                                   '-b:a', str(chosen_bitrate),
                                   '-id3v2_version', '3',
                                   str(mp3_output_path)]

                            print(f'{mvb_clrln}{Fore.LIGHTYELLOW_EX}Encoding... ({index}/{len(track_paths)})', end='', flush=True)
                            try:
                                result = subprocess.run(
                                    cmd, check=True, capture_output=True, text=True, encoding='utf-8'
                                )
                            except subprocess.CalledProcessError as e:
                                ask_exit(f'{Fore.RED}Error running ffmpeg!{Fore.RED}:\n'
                                         f'{e.stderr}', 30)

                    case '_':
                        ...
            ask_exit(f'{mvb_clrln}{Fore.LIGHTGREEN_EX}Done!{Fore.RESET}')

            # bitrate_avg = 0
            # for track_data in tracks_data:
            #     bitrate_avg += track_data['audio'][0]['bit_rate']
            # bitrate_avg /= len(track_paths)

            # print(f'{Fore.LIGHTCYAN_EX}'
            #       f'-----------------------------\n'
            #       f'Average bitrate: {int(bitrate_avg)}\n'
            #       f'-----------------------------\n')




if __name__ == '__main__':
    main()
