import subprocess as sp
import tkinter.filedialog


def cmd(shell_command):
    sp.run(shell_command, shell=True)


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


class RacoonUtilitiesDirectoryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


music_directory_path = "C:\\Users\\tobia\\Music"
artist_name = "Mark"

try:
    if sp.run(f'mkdir {music_directory_path}\\{artist_name}', shell=True, capture_output=True).returncode != 0:
        raise RacoonUtilitiesDirectoryError("Directory already exists")
except RacoonUtilitiesDirectoryError:
    print("Artist folder already exists")
else:
    sp.run(f'mkdir "{music_directory_path}\\{artist_name}"', shell=True)
print(sp.run(f'cd {music_directory_path}&&mkdir {artist_name}', shell=True, capture_output=True))