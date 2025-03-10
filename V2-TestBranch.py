import subprocess as sp
import tkinter.filedialog
import validators


# Dummy url 5 sec video
# https://www.youtube.com/watch?v=m9coOXt5nuw


def askExit():
    input("\nPress Enter to exit...")
    exit()


# url = input("Url: ")
# if not validators.url(url):
#	print("\nMust provide proper url, dumbass")
#	askExit()

primaryUrl = "https://www.youtube.com/playlist?list=PLhu_BwnCi_WausW4fZA-O8mB7fRGTShWZ"

if primaryUrl.find("list") != -1 or primaryUrl.find("playlist") != -1:
    isAPlaylist = True
else:
    isAPlaylist = False



if isAPlaylist:
    idCheck = sp.run(f'yt-dlp --flat-playlist --print id "{primaryUrl}" -i', shell=True, capture_output=True).stdout
    idList = str(idCheck)[1:-3].replace("'", "").split(sep="\\n")
    urlList = []
    for id in idList:
        urlList.append(f"https://www.youtube.com/watch?v={id}")

with open("C:/Users/tobia/Documents/Configurables/yt-dlp-helper-config.txt", "r") as config:
    configData = ""
    for line in config:
        configData += line

if configData.find("-P") != -1:
    downloadPath = configData[configData.find("-P") + 3:].replace('"', "")
    downloadPath = downloadPath[:downloadPath.find("\n")]
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
    proc = sp.Popen(cmd, stdout=sp.PIPE, universal_newlines=True)
    for outputLine in iter(proc.stdout.readline, ""):
        executeOutputData += outputLine
        if outputLine.find(" of ") != -1 or outputLine.find(" Destination: ") != -1 or outputLine.find("Merging") != -1 or outputLine.find("has already been downloaded") != -1:
            print(outputLine.replace("\n", ""))
    return executeOutputData


if isAPlaylist:
    #tempVar = "1"
    tempVar = input("\nDownloading a playlist. How to treat download options?"
                    "\n1 - Choose one options list for all videos in playlist"
                    "\n2 - Choose options for each video in playlist"
                    "\n: ")
    if tempVar == "1":
        options = " "
        x = 0
        while x == 0:
            tempOption = input(f"Options:{options}{optionsDescription}\n: ")
            if tempOption == "":
                x = 1
            else:
                if tempOption == "-d":
                    options += f"--download-sections *{input('Start: ')}-{input('End: ')} "
                elif tempOption == "-wt":
                    options += "--write-thumbnail "
                elif tempOption == "-res":
                    sp.run(f"yt-dlp -F {primaryUrl}")
                    tempID = input("\nID: ")
                    if tempID == "custom":
                        options += f"-f {input('Custom: ')} "
                    elif tempID == "":
                        tempID = input("\nID: ")
                    else:
                        options += f"-f bestaudio+{tempID} "
                elif tempOption == "-p":
                    path = tkinter.filedialog.askdirectory()
                    options += f"-P {path} "

                elif tempOption == "reset":
                    options = " "
                else:
                    options += tempOption + " "

        if options.find("-f ") != -1 and options.find("+") == -1:
            singleFile = True
        else:
            singleFile = False

        cmdOutputList = []

        for url in urlList:
            cmdOutputList.append(execute(f'yt-dlp {configData}{options} "{url}"'))
            print("\n")

        nameList = []
        for output in cmdOutputList:
            temp = output[output.find("[Merger]"):]
            nameList.append(temp[:temp.find("\n")])
        for i in range(0, len(nameList)):
            nameList[i] = str(nameList[i]).replace("[Merger] Merging formats into ", "").replace('"', "").replace(downloadPath.replace("/", "\\"), "").replace("\\", "")
            nameList[i] = nameList[i][:nameList[i].rfind(".")]

        print(f'Downloaded {len(nameList)} files from "{primaryUrl}":')
        for i in range(len(nameList)):
            print(f"{i+1} - {nameList[i]}")
        print(f'\nTo: {downloadPath.replace("/", "\\")}')
        askExit()
    elif tempVar == "2":
        cmdOutputList = []

        for url in urlList:
            options = " "
            x = 0
            while x == 0:
                tempOption = input(f"Options:{options}{optionsDescription}\n: ")
                if tempOption == "":
                    x = 1
                else:
                    if tempOption == "-d":
                        options += f"--download-sections *{input('Start: ')}-{input('End: ')} "
                    elif tempOption == "-wt":
                        options += "--write-thumbnail "
                    elif tempOption == "-res":
                        sp.run(f"yt-dlp -F {url}")
                        tempID = input("\nID: ")
                        if tempID == "custom":
                            options += f"-f {input('Custom: ')} "
                        elif tempID == "":
                            tempID = input("\nID: ")
                        else:
                            options += f"-f bestaudio+{tempID} "
                    elif tempOption == "-p":
                        path = tkinter.filedialog.askdirectory()
                        options += f"-P {path} "

                    elif tempOption == "reset":
                        options = " "
                    else:
                        options += tempOption + " "

            if options.find("-f ") != -1 and options.find("+") == -1:
                singleFile = True
            else:
                singleFile = False


            cmdOutputList.append(execute(f'yt-dlp {configData}{options} "{url}"'))
            print("\n")

        nameList = []
        for output in cmdOutputList:
            if output.find("has already been downloaded") != -1:
                name = str(output[:-1]).split("\n")
                nameList.append((name[-1].replace("[download] ", "").replace(" has already been downloaded", "").replace(downloadPath+"\\", "") + "Was already downloaded"))
            else:
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

sp.run("del C:\\Users\\tobia\\Downloads\\5_sec_video_ad_sample_2.mp4", shell=True)
sp.run("del C:\\Users\\tobia\\Downloads\\Countdown_5_seconds_timer.mp4", shell=True)
sp.run("del C:\\Users\\tobia\\Downloads\\Funniest_5_Second_Video_Ever.mp4", shell=True)
