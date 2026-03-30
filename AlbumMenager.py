from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.windowsUtilities import *
from colorama import Fore
import subprocess
import sys
import json


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

            for track_path in track_paths:
                tracks_data.append(get_media_file_data(track_path))

            format_names = []
            for track_data in tracks_data:
                format_names.append(track_data['format']['format_name'])
            format_names = list(dict(format_names))

            if all(has_video_stream(path) for path in track_paths):
                print(f'{Fore.LIGHTGREEN_EX}Cover image found in all audio files!{Fore.RESET}\n'
                      f'')


            if len(format_names) > 1:
                ...
            else:
                format_name = format_names[0]
                match format_name:
                    case 'flac':
                        ...
                    case 'mp3':
                        ...
                    case 'ogg':
                        ...
                    case _:
                        print(f'{Fore.LIGHTRED_EX} Unaccounted audio file format. May produce unexpected resoults\n'
                              f'(Be sure to understand lossy conversion)')

        case '2':  # Tracks to mp4
            ...
        case '3':  # Mp3
            ...





if __name__ == '__main__':
    main()
