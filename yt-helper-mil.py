from os import makedirs, mkdir

from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.windowsUtilities import *
from colorama import Fore
from datetime import datetime
import configparser
import subprocess
import validators
import sys

DEBUG = False


# https://youtu.be/YKsQJVzr3a8?si=8EV15smo14l7Aqg8

def main():
    now = datetime.now()

    # Format: year-month-day-hour:minute
    timestamp = now.strftime("%Y-%m-%d--%H-%M")

    # Update to latest stable yt-dlp
    print(f'{Fore.LIGHTCYAN_EX}Checking if yt-dlp.exe is up to date...{Fore.RESET}')
    try:
        process = subprocess.Popen(
            ['yt-dlp', '--update-to', 'nightly'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            text=True,
        )
        line_count = 0
        updated = False
        version = None

        for line in iter(process.stdout.readline, ''):
            print(f'{Fore.LIGHTYELLOW_EX}{line.strip()}{Fore.RESET}')

            if 'ERROR' in line:
                raise ConnectionError
            if 'Updating' in line:
                updated = True
            if 'Current version' in line:
                version = line[len('Current version: '):]
            if 'Latest version' in line:
                version = line[len('Latest version: '):]

            line_count += 1
        console_clear_n(line_count)

        if updated:
            print(f'{Fore.LIGHTGREEN_EX}'
                  f'Updated to: {version}\n'
                  f'{Fore.RESET}')
        else:
            print(f'{Fore.LIGHTGREEN_EX}'
                  f'Yt-dlp is up to date [{str(version).strip()}]\n'
                  f'{Fore.RESET}')
    except ConnectionError:
        print(f'{Fore.LIGHTRED_EX}Error updating yt-dlp to newest version!!!{Fore.RESET}')
        decision_temp = input(f'Continue with the current version? '
                              f'(It is highly recommended to abort and manually update yt-dlp to latest stable version)\n'
                              f'y/n\n: ')
        if decision_temp.lower() == 'n':
            ask_exit('')

    # Parse config
    config = configparser.ConfigParser(allow_no_value=True, delimiters='=')
    config.optionxform = str
    config.read("config.ini")

    configOptions_list = []
    for section in config.sections():
        if section == "DownloadPath":
            continue
        for key in config[section]:
            configOptions_list.append(key)
    configOptions = ' '.join(configOptions_list).strip()

    DownloadPath_keys = list(config['DownloadPath'].keys())
    echoOutput = subprocess.run(f'echo {DownloadPath_keys[0]}', shell=True, capture_output=True,
                                text=True).stdout.strip()
    echoOutput = echoOutput.replace('-P ', '').replace('%', '')
    downloadPath = Path(echoOutput)
    makedirs(downloadPath, exist_ok=True)
    batch_url_file_path = DownloadPath_keys[1]

    urlInput_count = 0
    batch = False
    while True:
        if urlInput_count == 0:
            print('Input "-batch" to download from the .txt file configurated in the .ini\n')
            print('Url: ', end='')
            url = input()
            if '-batch' in url:
                batch = True
                primaryUrl = batch_url_file_path
                break
            if validators.url(url):
                primaryUrl = url
                console_clear_n(1)
                print(f'{Fore.LIGHTGREEN_EX}'
                      f'Url: {url}'
                      f'{Fore.RESET}')
                break
            urlInput_count += 1

        if urlInput_count == 1:
            sys.stdout.write("\033[F\033[K")
            print(f'"{url}" is not a valid url, dumbass. Input a proper one: ', end='')
            url = input()
            if validators.url(url):
                primaryUrl = url
                console_clear_n(1)
                print(f'{Fore.LIGHTGREEN_EX}'
                      f'Url: {url}'
                      f'{Fore.RESET}')
                break
            urlInput_count += 1

        if urlInput_count >= 2:
            console_clear_n(1)
            print(f'Still wrong, you typed "{url}", try again: ', end='')
            url = input()
            if validators.url(url):
                primaryUrl = url
                console_clear_n(1)
                print(f'{Fore.LIGHTGREEN_EX}'
                      f'Url: {url}'
                      f'{Fore.RESET}')
                break
            urlInput_count += 1

    if batch:
        downloadPath = Path.joinpath(downloadPath, timestamp)
        makedirs(downloadPath, exist_ok=True)

    # Remove start_radio from url
    if 'start_radio' in primaryUrl:
        primaryUrl = primaryUrl[:primaryUrl.find('&list')]

    # Check if URL is a YouTube playlist
    isAPlaylist = False
    playlistFlags = ['list']
    if any(result in primaryUrl for result in playlistFlags):
        isAPlaylist = True

    # Define option dialogue
    optionsDescription = (
        'Enter options with a whitespace as a separator.\n'
        "---------------------------------------------------------------------------------------"
        "\n-d |  --download-sections  |  Downloads only selected time-frame  |  *{Start}-{End}  eg. *00:00-03:42"
        "\n-wt  |  --write-thumbnail  |  Saves the thumbnail in the same path as the file"
        "\n-res  |  Opens a dialogue window that allows for checking and choosing one of the available resolutions."
        "\n-p  |  Custom download path\n"
        "---------------------------------------------------------------------------------------"
    )
    playlistOptionsDescription = (
        'Enter options with a whitespace as a separator.\n'
        "---------------------------------------------------------------------------------------"
        "\n--write-thumbnail  |  -wt  |  Saves the thumbnails of each video in the same path as the file"
        "\n-res  |  !WARNING: downloading a playlist! -res will generate possible formats for every video in the playlist"
        "\n-p  |  Custom download path\n"
        "---------------------------------------------------------------------------------------"
    )

    if isAPlaylist:
        print(playlistOptionsDescription)
    else:
        print(optionsDescription)

    # Get tempOptions form OptionsDescription, replacing non-input related shortcut options with their full counterparts
    optionKeywords_short = [
        '-d',
        '-wt'
    ]
    optionKeywords_full = [
        '--download-sections',
        '--write-thumbnail'
    ]

    def replaceKeywords(string: str, old_list, new_list) -> str:
        for index in range(len(old_list)):
            string = string.replace(old_list[index], new_list[index])
        return string

    options = (replaceKeywords(input(f': '), optionKeywords_short, optionKeywords_full)).strip()
    print()

    # Check for custom options, get input if needed and add to tempOptions
    if '-res' in options:
        print(f'{Fore.LIGHTCYAN_EX}Fetching a table of available streams...{Fore.RESET}')
        result = subprocess.run(f'yt-dlp -F "{primaryUrl}"', capture_output=True, text=True)
        output = result.stdout.splitlines()

        start_index = None
        for index, line in enumerate(output):
            if line.strip().startswith('ID'):
                start_index = index
                break

        console_clear_n(1)  # go up one line and clear it
        if start_index is not None:
            output = output[start_index:]
        print("\n".join(output))

        print(
            'WARNING!\n'
            'Input both audio and video ids if you want both! Include one id for just one stream.\n'
            'Example: 234+ba\n'
            'id: ', end=''
        )
        tempInput = input('')
        if tempInput != '':
            options = options.replace('-res', f'-f {tempInput}')
        else:
            tempInput = input('Did you mean to press enter?\n'
                              'Press enter again if yes, input an id if no\n: ')
            if tempInput == '':
                options = options.replace('-res', '')
            else:
                options = options.replace('-res', f'-f {tempInput}')

    if '-f' in options:
        configOptions = configOptions.replace('-t mp4', '')

    if '-p' in options:
        try:
            downloadPath = win_dir_path('Download destination')
            options = options.replace(f'-p ', f'')
        except (Exception,):
            options = options.replace(f'-p ', f'')
            print(f'{Fore.LIGHTRED_EX}[Error] Something went wrong while setting custom download folder.\n'
                  f'Falling back to default...{Fore.RESET}')

    finalCommand_list = [
        'yt-dlp',
        f'{configOptions}',
        f'{options}',
        f'-P "{downloadPath}"',
        f'"{primaryUrl}"'
    ]
    if batch:
        finalCommand_list.insert(-1, '-a ')
    finalCommand = ' '.join(finalCommand_list).replace('  ', ' ')

    if DEBUG:

        debugList = [primaryUrl, isAPlaylist, downloadPath, options, configOptions, finalCommand]
        print()
        for i in debugList:
            print(f'{Fore.LIGHTCYAN_EX}'
                  f'[debug] '
                  f'{Fore.RESET}'
                  f'|{i}|')
        print()

    try:
        process = subprocess.Popen(
            finalCommand,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            text=True,
        )
        line_count = 0
        lastLine = process.stdout.readline
        for line in iter(process.stdout.readline, ''):

            if '[download]' in line:
                if ' Destination: ' in line:
                    filePath = Path(line.replace('[download] Destination: ', '').strip())
                    print(f'\n{Fore.LIGHTCYAN_EX}'
                          f'[download]'
                          f'{Fore.RESET} '
                          f'{Fore.LIGHTYELLOW_EX}'
                          f'{filePath.name}'
                          f'{Fore.LIGHTYELLOW_EX}')
                line = line.replace('[download]', f'{Fore.LIGHTCYAN_EX}[download]{Fore.RESET}').strip()
                print('\r' + line + ' ' * (abs(len(lastLine) - len(line))), end='')
            lastLine = line
            line_count += 1
    except (Exception,) as e:
        print(e)

    if DEBUG:
        filePath.unlink()


if __name__ == '__main__':
    main()