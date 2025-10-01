import configparser
import subprocess as sp
import validators
import win32clipboard
import sys
from Raccoon import *

# Parse config
config = configparser.ConfigParser(allow_no_value=True, delimiters='=')
config.optionxform = str
config.read("config.ini")

configOptionList = ''
for section in config.sections():
    if section == "DownloadPath":
        continue
    for key in config[section]:
        configOptionList += key + ' '

for key in config['DownloadPath']:
    downloadPath = f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace(
        '\n', '')[3:]

# Get clipboard data
try:
    win32clipboard.OpenClipboard()
    clipBoardData = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
except (Exception,):
    clipBoardData = 'Error'

# If clipboards is a URL use it, if not, get URL
if validators.url(clipBoardData):
    print("Found a valid url link in the clipboard!\nUsing that one.")
    primaryUrl = clipBoardData
else:
    while True:
        url = input("Url: ")
        if validators.url(url):
            primaryUrl = url
            break
        elif url == "":
            sys.stdout.write("\033[F\033[K")
            pass

        else:
            while True:
                sys.stdout.write("\033[F\033[K")
                url = input(f'"{url}" is not a valid url, dumbass. Input a proper one: ')
                if validators.url(url):
                    primaryUrl = url
                    break
                elif url == "":
                    sys.stdout.write("\033[F\033[K")
                    pass

                else:
                    sys.stdout.write("\033[F\033[K")
                    while True:
                        url = input(f'Still wrong, you typed "{url}", try again: ')
                        if validators.url(url) and url != "":
                            primaryUrl = url
                            break
                        sys.stdout.write("\033[F\033[K")
                    if primaryUrl == url:
                        break
            break

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

if isAPlaylist is True:
    print(playlistOptionsDescription)
else:
    print(optionsDescription)

# Get tempOptions form OptionsDescription, replacing non-input related shortcut options with their full counterparts
options = ((input(f': ')
            .replace('-d', '--download-sections')
            .replace('-wt', "--write-thumbnail"))
           .strip())

# Check for custom options, get input if needed and add to tempOptions
if options.find("-res") != -1:
    sp.run(f'yt-dlp -F {primaryUrl}')

    tempInput = input(
        "WARNING!\n"
        "Input both audio and video ids if you want both! Include one id for just one stream.\n"
        "Example: 234+ba\n"
        "id: "
    )
    if tempInput != '':
        options = options.replace('-res', f'-f {tempInput}')
    else:
        tempInput = input('Did you mean to press enter?\nPress enter again if yes, id if no\n: ')
        if tempInput == '':
            options = options.replace('-res', '')
        else:
            options = options.replace('-res', f'-f {tempInput}')

if options.find("-p") != -1:
    try:
        path = options[options.find('-p') + 3:]
        if path.find('-') != -1:
            path = path[:path.find('-')]
        if path != '':
            options = options.replace(f'-p {path}', f'')
            downloadPath = path
        else:
            path = Ru.winDirPath('Download destination')
            options = options.replace(f'-p ', f'')
            downloadPath = path
    except ():
        path = Ru.winDirPath('Download destination')
        downloadPath = path
        oldPath = options[options.find('-p') + 3:]
        if oldPath.find('-') != -1:
            oldPath = oldPath[:oldPath.find('-')].strip()
        options = options.replace(f'-p {oldPath}', f'')


print(primaryUrl)
print(isAPlaylist)
print(downloadPath)
print(configOptionList)
