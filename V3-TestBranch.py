import subprocess as sp
import tkinter.filedialog
import validators
import win32clipboard
import os
import threading
import time

options = ""
def askExit():
    def inputExit():
        input("\nPress Enter to exit...")
        os._exit()

    def TimeExit():
        time.sleep(5)
        print("balls")
        os._exit()

    if __name__ =="__main__":
        t1 = threading.Thread(target=inputExit, args=())
        t2 = threading.Thread(target=TimeExit, args=())

        t1.start()
        t2.start()

        t1.join()
        t2.join()


win32clipboard.OpenClipboard()
clipBoardData = win32clipboard.GetClipboardData()
win32clipboard.CloseClipboard()

if validators.url(clipBoardData) is True:
    primaryUrl = clipBoardData
else:
    primaryUrl = input("Url: ")
    if not validators.url(primaryUrl):
        print("\nMust provide proper url, dumbass")
        askExit()

if primaryUrl.find("list") != -1:
    isAPlaylist = True
else:
    isAPlaylist = False

if isAPlaylist:
    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout
    idList = str(idCheck)[1:-3].replace("'", "").split(sep="\\n")
    urlList = []
    for id in idList:
        urlList.append(f"https://www.youtube.com/watch?v={id}")

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

configData = configData.replace("Write options on new lines:", "").replace("\n", " ")
configData = configData[1:]

optionsDescription = (
    "\n---------------------------------------------------------------------------------------\n"
    "reset  |  Resets current options"
    "\nEnter to move on, arguments different from the list below will be added as written."
    "\n---------------------------------------------------------------------------------------"
    "\n--download-sections  |  -d  |  Downloads only selected time-frame  |  Start-End"
    "\n--write-thumbnail  |  -wt  |  Saves the thumbnail in the same path as the file"
    "\n-res  |  Custom resolution. 'custom' in Id: to write own -f argument"
    "\n-p  |  Custom path"
)


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

    nameList = []
    for output in cmdOutputList:
        temp = output[output.find("[Merger]"):]
        nameList.append(temp[:temp.find("\n")])
    for i in range(0, len(nameList)):
        nameList[i] = str(nameList[i]).replace("[Merger] Merging formats into ", "").replace('"', "").replace(
            downloadPath.replace("/", "\\"), "").replace("\\", "")
        nameList[i] = nameList[i][:nameList[i].rfind(".")]

    print(f'Downloaded {len(nameList)} files from "{primaryUrl}":')
    for i in range(len(nameList)):
        print(f"{i + 1} - {nameList[i]}")
    print(f'\nTo: {downloadPath.replace("/", "\\")}')
    askExit()
else:

    cmdOutput = (execute(f'yt-dlp {configData}{options} "{primaryUrl}"'))

print(cmdOutput)
