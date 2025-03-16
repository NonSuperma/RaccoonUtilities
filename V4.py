import configparser
import subprocess as sp
import tkinter.filedialog
import validators
import win32clipboard


def askExit():
    input()
    exit()


def winPath():
    tempPath = tkinter.filedialog.askdirectory().replace('/', '\\').strip()
    return tempPath


def execute(cmd):
    executeOutputData = ""
    proc = sp.Popen(cmd, stdout=sp.PIPE, universal_newlines=True, shell=True)
    lastLine = iter(proc.stdout.readline, '')
    for outputLine in iter(proc.stdout.readline, ""):
        executeOutputData += outputLine
        if outputLine.find(" Destination: ") != -1 or outputLine.find("Merging") != -1 or outputLine.find(
                "has already been downloaded") != -1:
            fileName = outputLine[outputLine.rfind('\\')+1:].replace('\n', '')
            if fileName.rfind('.f') != -1:
                print(fileName[fileName.rfind('.f')+5])
                extension = fileName[:fileName.rfind('.')]
                fileName = fileName.replace(extension, '')[:fileName.rfind('.')]
                fileName += extension
            print(fileName)
            print(outputLine.replace("\n", ""))
        if outputLine.find(" of ") != -1 and lastLine.find(" of ") != -1:
            print('\r' + outputLine.replace('\n', ''), end='')
        elif outputLine.find(" of ") != -1:
            print(outputLine.replace('\n', ''), end="")
        lastLine = outputLine
    return executeOutputData


# Get clipboard data if available
try:
    win32clipboard.OpenClipboard()
    clipBoardData = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
except (Exception,):
    clipBoardData = 'Error'

# Get the primary url/urls
if validators.url(clipBoardData) == True:
    print("Found a valid url link in the clipboard!\nUsing that one.")
    primaryUrl = clipBoardData
else:
    a = 0
    while a == 0:
        url = input("Url: ")
        if validators.url(url) == True and url != '':
            primaryUrl = url
            a = 1
        else:
            print("Wrong url, dumbass\nInput a proper one")

# Check if url is a yt playlist, if yes, create urlList with a list of urls that will be used
if primaryUrl.find("list") != -1 and primaryUrl.lower().find("youtu") != -1:

    isAPlaylist = True
    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout.decode().split()
    urlList = []
    for id in idCheck:
        urlList.append(f"https://www.youtube.com/watch?v={id}")
    print(f"Downloading {len(urlList)} videos from a Youtube playlist\n")
else:
    isAPlaylist = False

# Read config, create downloadPath and configOptionList
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
    downloadPath = f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace('\n', '')[3:]


def getUserOptions():
    global downloadPath
    # Define option dialogue
    optionsDescription = (
        'Enter options with a whitespace as a separator.\n'
        "---------------------------------------------------------------------------------------"
        "\n--download-sections  |  -d  |  Downloads only selected time-frame  |  *{Start}-{End}"
        "\n--write-thumbnail  |  -wt  |  Saves the thumbnail in the same path as the file"
        "\n-res  |  Custom resolution."
        "\n-p  |  Custom path\n"
        "---------------------------------------------------------------------------------------"
    )
    print(optionsDescription)

    # Get tempOptions form OptionsDescription, replacing non-input related shortcut options with their full counterparts
    options = input(f': ').replace('-d', '--download-sections').replace('-wt', "--write-thumbnail")
    try:
        if options[-1] != ' ':
            options += ' '
    except (IndexError,):
        pass

    # Check for custom options, get input if needed and add to tempOptions
    if options.find("-res") != -1:
        sp.run(f'yt-dlp -F {primaryUrl}')
        options = options.replace('-res', '-f ' + input("WARNING!\nInput both audio and video ids if you want both! Include one id for just one stream.\nExample: 234+ba\nid: "))
    if options.find("-p") != -1:
        try:
            path = options[options.find('-p')+3:]
            if path.find('-') != -1:
                path = path[:path.find('-')]
            if path != '':
                options = options.replace(f'-p {path}', f'')
                downloadPath = path
            else:
                path = winPath()
                options = options.replace(f'-p ', f'')
                downloadPath = path
        except ():
            path = winPath()
            downloadPath = path
            oldPath = options[options.find('-p') + 3:]
            if oldPath.find('-') != -1:
                oldPath = oldPath[:oldPath.find('-')].strip()
            options = options.replace(f'-p {oldPath}', f'')
    return options
userOptions = getUserOptions()
if downloadPath[-1] != ' ':
    downloadPath += ' '

execute(f'yt-dlp -P {downloadPath}{configOptionList}{userOptions}"{primaryUrl}"')
#sp.run(f'yt-dlp -P {downloadPath}{configOptionList}{userOptions}"{primaryUrl}"', shell=True)
#print(f'yt-dlp -P {downloadPath}{configOptionList}{userOptions}"{primaryUrl}"')
