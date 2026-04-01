from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.windowsUtilities import *
from colorama import Fore, Back
import subprocess
import sys
import json
from pathlib import Path


def has_video_stream(file_path):
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

def user_album_name_choice_dialogue(folder_name: str) -> str:
    userChoice = input(
        f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} The selected songs are in a folder called {Fore.GREEN}{folder_name}{Fore.RESET}\n'
        f'       Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n'
        f'       {Fore.LIGHTBLUE_EX}[]{Fore.RESET} gets converted into {Fore.GREEN}{folder_name}{Fore.RESET}\n'
        f'       {Fore.LIGHTBLUE_EX}--full{Fore.RESET} removes {Fore.LIGHTBLUE_EX}[Full Album]{Fore.RESET} from the final name\n'
        f'       : '
    )

    if userChoice == '':
        album_name = folder_name + ' [Full Album]'
    elif userChoice == '--full':
        album_name = folder_name
    else:
        album_name = userChoice

        if '[]' in album_name:
            album_name = album_name.replace('[]', workingFolderName)

        if '--full' in album_name:
            if ' --full' in album_name:
                album_name = album_name.replace(' --full', '')
            if ' --full ' in album_name:
                album_name = album_name.replace(' --full ', '')
            if '--full ' in album_name:
                album_name = album_name.replace('--full ', '')
            album_name = album_name.replace('--full', '')
        else:
            album_name += ' [Full Album]'
    return album_name


def main():

    choices_description = ('1 - Album to mp4 - Create an mp4 file from multiple audio files and optionally a cover image\n'
                           '2 - Tracks to mp4 - Create seperate mp4 file from multiple or one flac files and optionally a cover image\n'
                           '3 - Mp3 - Create an mp3 file from any losless audio file\n')

    print(choices_description)
    userChoice = input(': ')
    console_clear_n(choices_description.count('\n') + 2)

    match userChoice:
        case '1':  # Album to mp4
            track_paths = win_files_path('Tracks', 'audio')
            tracks_data = []

            folder_path = track_paths[0].parent

            for track_path in track_paths:
                tracks_data.append(get_media_file_data(track_path))

            format_names = []
            for track_data in tracks_data:
                format_names.append(track_data['format']['format_name'])
            format_names = list(set(format_names))

            if all(has_video_stream(path) for path in track_paths):
                first_track_data = tracks_data[0]
                print(f'{Fore.LIGHTGREEN_EX}Embeded cover image found in all audio files!{Fore.RESET}\n'
                      f'{Fore.LIGHTMAGENTA_EX}'
                      f'------------------------------\n'
                      f'Resolution: {first_track_data['video'][0]['width']}x{first_track_data['video'][0]['height']}\n'
                      f'Codec name: {first_track_data['video'][0]['codec_name']}\n'
                      f'------------------------------'
                      f'{Fore.RESET}')
                print(f'Use imbeded image as cover going forward? y/n\n'
                      f'("No" will let you choose the cover file manually)')
                userChoice = input(f':').lower()

                cover_path = None
                cover_extracted = False
                if userChoice == 'y':
                    cover_extracted = True
                    cover_filename = 'cover_extracted.png'
                    cover_path = Path.joinpath(folder_path, cover_filename)

                    cmd = [
                        'ffmpeg',
                        '-y',
                        '-v', 'error',
                        '-i', str(track_paths[0]),
                        '-map', '0:v:0',
                        '-frames:v', '1',
                        '-update', '1',
                        str(cover_path)
                    ]
                    subprocess.run(cmd)

                else:
                    cover_path = win_file_path('Cover', 'image')


            if len(format_names) > 1:
                print('Mixed formats')
            else:
                format_name = format_names[0]
                match format_name:
                    case 'flac':
                        print(f'{Fore.LIGHTGREEN_EX}All files are FLAC{Fore.RESET}')

                        folder_name = folder_path.name
                        album_name = user_album_name_choice_dialogue(folder_name)

                        print(f'Album filename chosen: {Fore.LIGHTBLUE_EX}"{album_name}"{Fore.RESET}\n')

                        # with open(workingFolderPath / 'audio_input_list.txt', 'w+',
                        #           encoding='utf-8') as audio_input_list:
                        #     for tempAudioPath in tempAudioPaths:
                        #         audio_input_list.write(f"file '{str(tempAudioPath)}'\n")

                        temp_track_file = Path.joinpath(folder_path, 'temp_track_file.txt')

                        with open(temp_track_file, 'w+', encoding='utf-8') as file:
                            for track_path in track_paths:
                                file.write(f'file "{str(track_path)}"\n')



                        concaded_track_path = folder_path / f'{album_name}.flac'
                        cmd = ['ffmpeg', '-y',
                               'loglevel', 'fatal'
                               '-f', 'concad',
                               '-safe', '0',
                               '-i', ]

                        # subprocess.run(f'ffmpeg '
                        #                f'-y '
                        #                f'-loglevel fatal '
                        #                f'-f concat '
                        #                f'-safe 0 '
                        #                f'-i "{str(workingFolderPath.joinpath('audio_input_list.txt'))}" '
                        #                f'"{finalConcadFilePath}"',
                        #                capture_output=True)

                    case 'mp3':
                        print(f'\n{Fore.LIGHTGREEN_EX}All files are MP3{Fore.RESET}')

                        bitrate_avg = 0
                        for track_data in tracks_data:
                            bitrate_avg += track_data['audio'][0]['bit_rate']
                        bitrate_avg /= len(track_paths)

                        print(f'{Fore.LIGHTMAGENTA_EX}'
                              f'------------------------------\n'
                              f'Average bitrate: {int(bitrate_avg)}\n'
                              f'------------------------------'
                              f'{Fore.RESET}')

                        chosen_mp3_bitrate = input('Choose the bitrate of the output mp4 file. "k" converts to 1000, ex. 320k = 320000')
                        if "k" in chosen_mp3_bitrate:
                            chosen_mp3_bitrate = (int(chosen_mp3_bitrate.strip().replace('k', '')) * 1000)
                        else:
                            chosen_mp3_bitrate = int(chosen_mp3_bitrate)

                    case 'ogg':
                        print(f'{Fore.LIGHTGREEN_EX}All files are ogg{Fore.RESET}')
                    case _:
                        print(f'{Fore.LIGHTYELLOW_EX}[Warning] Unaccounted audio file format. May produce unexpected results\n'
                              f'(Be sure to understand lossy conversion){Fore.RESET}')

            if cover_extracted:
                cover_path.unlink()

        case '2':  # Tracks to mp4
            ...
        case '3':  # Mp3
            ...





if __name__ == '__main__':
    main()
