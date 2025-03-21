import subprocess as sp
import tkinter.filedialog
from vidMaker import makeVideo
from albumMaker import makeAlbum


class RacoonUtilitiesDirectoryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def askExit():
    input("Press enter to exit...")
    exit()


def winDirPath():
    tempPath = tkinter.filedialog.askdirectory().replace('/', '\\').strip()
    return tempPath


def winFilePath():
    tempPath = tkinter.filedialog.askopenfilename().replace('/', '\\').strip()
    return tempPath


def winFilesPath():
    tempPaths = list(tkinter.filedialog.askopenfilenames())
    for i in range(len(tempPaths)):
        tempPaths[i] = tempPaths[i].replace('/', '\\')
    return tempPaths


def createFullAlbum(image_path, audio_paths, album_name, artist_name, music_directory_path):
    extensionList = []
    for audioFilePath in audio_paths:
        extensionList.append(audioFilePath[audioFilePath.rfind(".") + 1:])
    extensionList = list(dict.fromkeys(extensionList))

    if len(extensionList) > 1:
        audioFolder = "Audio"
    else:
        audioFolder = extensionList[0]

    try:
        if sp.run(f'mkdir {music_directory_path}\\{artist_name}', shell=True, capture_output=True).returncode != 0:
            raise RacoonUtilitiesDirectoryError
    except (RacoonUtilitiesDirectoryError,):
        pass
    else:
        sp.run(f'mkdir {music_directory_path}\\{artist_name}', shell=True)


imagePath = tkinter.filedialog.askopenfilename().replace('/', '\\').strip()
audioPaths = winFilesPath()
albumName = "Nigger"
artistName = "EvenMoreNigger"
musicDirectoryPath = "C:\\Users\\tobia\\Music"

createFullAlbum(imagePath, audioPaths, albumName, artistName, musicDirectoryPath)
