from Raccoon.errors import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.outputClasses import *
from Raccoon.windowsUtilities import *
from Raccoon.outputClasses import *
from colorama import Fore
import configparser
import subprocess
import validators
import pyperclip
import sys

DEBUG = True

# https://youtu.be/YKsQJVzr3a8?si=8EV15smo14l7Aqg8

# Update to latest stable yt-dlp
print(f'{Fore.LIGHTCYAN_EX}Checking if yt-dlp.exe is up to date...{Fore.RESET}')
try:
    process = subprocess.Popen(
        ['yt-dlp', '-U'],
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
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
    process.wait()
    for i in range(line_count):
        sys.stdout.write("\033[F\033[K")
    if updated:
        print(f'{Fore.LIGHTGREEN_EX}'
              f'Updated to: {version}\n'
              f'{Fore.RESET}')
    else:
        print(f'{Fore.LIGHTGREEN_EX}'
              f'Yt-dlp is up to date\n'
              f'{Fore.RESET}')
except ConnectionError:
    print(f'{Fore.LIGHTRED_EX}Error updating yt-dlp to newest version!!!{Fore.RESET}')
    decision_temp = input(f'Continue with the current version? y/n\n: ')
    if decision_temp.lower() == 'n':
        askExit('')


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

for key in config['DownloadPath']:
    echoOutput = subprocess.run(f'echo {key}', shell=True, capture_output=True).stdout.decode()
    downloadPath = Path(str(echoOutput).replace('-P ', '').replace('%', ''))
# Get clipboard data
try:
    clipBoardData = pyperclip.paste()
except (Exception,):
    clipBoardData = None

# If clipboards is a URL use it, if not, get URL
if validators.url(clipBoardData):
    primaryUrl = clipBoardData

    print(f'{Fore.LIGHTGREEN_EX}Found a valid url link in the clipboard!{Fore.RESET}\n'
          f'{Fore.LIGHTCYAN_EX}{primaryUrl}{Fore.RESET} - using that one.\n')
else:
    urlInput_count = 0
    while True:
        if urlInput_count == 0:
            print('Url: ', end='')
            url = input()
            if validators.url(url):
                primaryUrl = url
                sys.stdout.write("\033[F\033[K")
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
                sys.stdout.write("\033[F\033[K")
                print(f'{Fore.LIGHTGREEN_EX}'
                      f'Url: {url}'
                      f'{Fore.RESET}')
                break
            urlInput_count += 1

        if urlInput_count >= 2:
            sys.stdout.write("\033[F\033[K")
            print(f'Still wrong, you typed "{url}", try again: ', end='')
            url = input()
            if validators.url(url):
                primaryUrl = url
                sys.stdout.write("\033[F\033[K")
                print(f'{Fore.LIGHTGREEN_EX}'
                      f'Url: {url}'
                      f'{Fore.RESET}')
                break
            urlInput_count += 1

# Check if URL is a YouTube playlist
isAPlaylist = False
playlistFlags = ['start_radio', 'list']
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
    for index in range(len((old_list))):
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

    sys.stdout.write("\033[F\033[K")  # go up one line and clear it
    if start_index is not None:
        print("\n".join(output[start_index:]))

    tempInput = input(
        'WARNING!\n'
        'Input both audio and video ids if you want both! Include one id for just one stream.\n'
        'Example: 234+ba\n'
        'id: '
    )
    if tempInput != '':
        options = options.replace('-res', f'-f {tempInput}')
    else:
        tempInput = input('Did you mean to press enter?\nPress enter again if yes, input an id if no\n: ')
        if tempInput == '':
            options = options.replace('-res', '')
        else:
            options = options.replace('-res', f'-f {tempInput}')

if '-f' in options:
    configOptions = configOptions.replace('-t mp4', '')

if '-p' in options:
    try:
        downloadPath = winDirPath('Download destination')
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

finalCommand = ' '.join(finalCommand_list).replace('  ', ' ')

if DEBUG:

    debugList = [primaryUrl, isAPlaylist, downloadPath, options, configOptions]
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
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
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
            print(line.replace('[download]', f'{Fore.LIGHTCYAN_EX}[download]{Fore.RESET}').strip())
            if '% of' in line:
                sys.stdout.write("\033[F\033[K")

        lastLine = line
except (Exception,) as e:
    print(e)

