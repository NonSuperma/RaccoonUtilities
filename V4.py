import configparser
import subprocess as sp
from tkinter import filedialog, Tk
import validators
import win32clipboard


class RacoonUtilitiesMissingInputError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RacoonUtilitiesDirectoryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def makeVideo(image_input_path, sound_input_paths, output_path):
    if image_input_path == "" or sound_input_paths == "":
        raise RacoonUtilitiesMissingInputError("No input")

    if output_path == '':
        output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]

    if len(sound_input_paths) == 1:
        sound_input_paths = sound_input_paths[0]
        name = sound_input_paths[sound_input_paths.rfind('\\') + 1:sound_input_paths.rfind('.')]

        sp.run(
            f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{name}.mp4"',
            shell=True)
    else:
        names = []
        for INDEX in range(0, len(sound_input_paths)):
            names.append(
                sound_input_paths[INDEX][sound_input_paths[INDEX].rfind("\\"):sound_input_paths[INDEX].rfind(".")])
        print(names)

        for INDEX in range(len(names)):
            sp.run(
                f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths[INDEX]}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{names[INDEX]}.mp4"',
                shell=True)


def makeAlbum(image_input_path, sound_input_paths, final_filename, output_path):
    if image_input_path == "" or sound_input_paths == "" or final_filename == "":
        raise RacoonUtilitiesMissingInputError("No input")

    if output_path == '':
        output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]
    print(output_path)

    inputPath = ''
    for i in sound_input_paths:
        inputPath += f'-i "{i.replace('/', '\\')}" '

    preConcat = ''
    for i in range(0, len(sound_input_paths)):
        preConcat += f'[{i}:a]'

    extension = sound_input_paths[0][sound_input_paths[0].rfind('.'):]

    sp.run(
        f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" {output_path}\\output{extension}',
        shell=True)
    sp.run(f'ren "{output_path}\\output{extension}" "{final_filename + extension}"', shell=True)

    sp.run(
        f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{output_path}\\{final_filename + extension}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{final_filename}.mp4"',
        shell=True)


def askExit():
    input("Press enter to exit...")
    exit()


def mkFolder(path, folder_name):
    try:
        if sp.run(f'mkdir {path}\\{folder_name}', shell=True, capture_output=True).returncode != 0:
            raise RacoonUtilitiesDirectoryError(f'Folder {folder_name} already exists')
    except RacoonUtilitiesDirectoryError:
        print(f'Folder {folder_name} already exists')
    else:
        sp.run(f'mkdir {path}\\{folder_name}', shell=True, capture_output=True)


def winDirPath(message):
    root = Tk()
    root.lift()
    root.withdraw()
    tempPath = filedialog.askdirectory(title=message, parent=root).replace('/', '\\').strip()
    return tempPath


def winFilePath(message):
    root = Tk()
    root.lift()
    root.withdraw()
    tempPath = filedialog.askopenfilename(title=message, parent=root).replace('/', '\\').strip()
    return tempPath


def winFilesPath(message):
    root = Tk()
    root.lift()
    root.withdraw()
    tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
    for i in range(len(tempPaths)):
        tempPaths[i] = tempPaths[i].replace('/', '\\')
    return tempPaths

# Yeaaah...
def execute(cmd):
    executeOutputData = ""
    proc = sp.Popen(cmd, stdout=sp.PIPE, universal_newlines=True, shell=True)
    lastLine = iter(proc.stdout.readline, '')
    for outputLine in iter(proc.stdout.readline, ""):
        executeOutputData += outputLine
        outputLine = outputLine.replace('[download]', f'{Bcolors.OKGREEN}[download]{Bcolors.ENDC}').replace('[Merger]', f'{Bcolors.OKCYAN}[Merger]{Bcolors.ENDC}')
        if outputLine.find(" Destination: ") != -1 or outputLine.find("Merging") != -1 or outputLine.find(
                "has already been downloaded") != -1:
            fileName = outputLine[outputLine.rfind('\\') + 1:].replace('\n', '')
            if fileName.rfind('.f') != -1:
                extension = fileName[fileName.rfind('.'):]
                fileName = fileName.replace(extension, '')
                fileName = fileName[:fileName.rfind('.')]
                fileName += extension
            if outputLine.find('Downloading item') != 1:
                print(f'\n\033[93m{fileName}\033[0m')
            else:
                print(f'\033[93m{fileName}\033[0m')
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
if validators.url(clipBoardData):
    print("Found a valid url link in the clipboard!\nUsing that one.")
    primaryUrl = clipBoardData
else:
    a = 0
    while a == 0:
        url = input("Url: ")
        if validators.url(url) and url != '':
            primaryUrl = url
            a = 1
        else:
            print("Wrong url, dumbass\nInput a proper one")

# Check if url is a yt playlist, if yes, create urlList with a list of urls that will be used
if primaryUrl.find("list") != -1 and primaryUrl.lower().find("youtu") != -1:

    isAPlaylist = True
    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True,
                     capture_output=True).stdout.decode().split()
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
    downloadPath = f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace(
        '\n', '')[3:]


def getUserOptions():
    global downloadPath
    # Define option dialogue
    optionsDescription = (
        'Enter options with a whitespace as a separator.\n'
        "---------------------------------------------------------------------------------------"
        "\n--download-sections  |  -d  |  Downloads only selected time-frame  |  *{Start}-{End}"
        "\n--write-thumbnail  |  -wt  |  Saves the thumbnail in the same path as the file"
        "\n-res  |  Custom resolution."
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
    global isAPlaylist
    if isAPlaylist is True:
        print(playlistOptionsDescription)
    else:
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
        options = options.replace('-res', '-f ' + input(
            "WARNING!\nInput both audio and video ids if you want both! Include one id for just one stream.\nExample: 234+ba\nid: "))
    if options.find("-p") != -1:
        try:
            path = options[options.find('-p') + 3:]
            if path.find('-') != -1:
                path = path[:path.find('-')]
            if path != '':
                options = options.replace(f'-p {path}', f'')
                downloadPath = path
            else:
                path = winDirPath('Download destination')
                options = options.replace(f'-p ', f'')
                downloadPath = path
        except ():
            path = winDirPath('Download destination')
            downloadPath = path
            oldPath = options[options.find('-p') + 3:]
            if oldPath.find('-') != -1:
                oldPath = oldPath[:oldPath.find('-')].strip()
            options = options.replace(f'-p {oldPath}', f'')
    return options


if downloadPath[-1] != ' ':
    downloadPath += ' '

execute(f'yt-dlp -P {downloadPath}{configOptionList}{getUserOptions()}"{primaryUrl}"')

