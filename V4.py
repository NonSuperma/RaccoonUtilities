import configparser
import subprocess as sp
import tkinter.filedialog
import validators
import win32clipboard


def askExit():
    input()
    exit()


def winPath():
    path = tkinter.filedialog.askdirectory().replace('/', '\\')
    return path


def execute(cmd):
    executeOutputData = ""
    proc = sp.Popen(cmd, stdout=sp.PIPE, universal_newlines=True, shell=True)
    lastLine = iter(proc.stdout.readline, '')
    for outputLine in iter(proc.stdout.readline, ""):
        executeOutputData += outputLine
        if outputLine.find(" Destination: ") != -1 or outputLine.find("Merging") != -1 or outputLine.find(
                "has already been downloaded") != -1:
            print('\n' + outputLine.replace("\n", ""))
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
if validators.url(clipBoardData) is True:
    print("Url found in user's clipboard, using that one\n")
    primaryUrl = clipBoardData
else:
    primaryUrl = input("Url: ")
    if validators.url(primaryUrl) is False:
        print("Input a proper url, dumbass")
        askExit()

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
    configOptionList += f'{sp.run(f'echo {key}', shell=True, capture_output=True, universal_newlines=True).stdout.replace('%', '')} '.replace('\n', '')

sp.run(f'yt-dlp {configOptionList}"{primaryUrl}"', shell=True)
# print(f'yt-dlp {configOptionList}"{primaryUrl}"')

