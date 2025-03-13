import subprocess as sp
import tkinter.filedialog
import validators
import win32clipboard


options = ""


def askExit():
    input()
    exit()


win32clipboard.OpenClipboard()
clipBoardData = win32clipboard.GetClipboardData()
win32clipboard.CloseClipboard()

if validators.url(clipBoardData) is True:
    print("Url found in clipboard\nLoaded!")
    primaryUrl = clipBoardData
else:
    primaryUrl = input("Url: ")
    if not validators.url(primaryUrl):
        print("\nMust provide proper url, dumbass")
        askExit()

if primaryUrl.find("list") != -1:
    isAPlaylist = True
    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout.decode().split()
    urlList = []
    for id in idCheck:
        urlList.append(f"https://www.youtube.com/watch?v={id}")
else:
    isAPlaylist = False

with open("yt-dlp-helper-config.txt", "r") as config:
    configData = ""
    for line in config:
        configData += line

if configData.find("-P") != -1:
    downloadPath = configData[configData.find("-P") + 3:].replace('"', "")
    downloadPath = downloadPath[:downloadPath.find("\n")]
    downloadPath = sp.run(f'echo {downloadPath}', shell=True, capture_output=True).stdout.decode("utf-8")
else:
    downloadPath = ""
    tempVar = input(
        "ERROR: Download path not specified in config file.\nTemporary download path? y/n for dialogue window, "
        "or just path to directory: ")
    if tempVar == "y":
        downloadPath = tkinter.filedialog.askdirectory()
    elif tempVar == "n":
        askExit()
    else:
        downloadPath = tempVar

configData = configData[1:].replace("Write options on new lines:", "").replace("\n", " ")


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


if isAPlaylist is True:
    cmdOutputList = []

    for url in urlList:
        cmdOutputList.append(execute(f'yt-dlp {configData}{options} "{url}"'))
        print("\n")
else:
    cmdOutput = (execute(f'yt-dlp {configData}{options} "{primaryUrl}"'))
    name = sp.run(f'yt-dlp --simulate --print "%(title)s" {primaryUrl}', shell=True, capture_output=True).stdout.decode().replace("\n", "")


# print(pf'yt-dlp {configData}{options} "{primaryUrl}"')
