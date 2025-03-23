import subprocess as sp
from tkinter import filedialog, Tk

root = Tk()
root.lift()
root.withdraw()

def cmd(shell_command):
	sp.run(shell_command, shell=True)


class RacoonUtilitiesMissingInputError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


def askExit():
	input("Press enter to exit...")
	exit()


def winDirPath(message):
	tempPath = filedialog.askdirectory(title=message, parent=root).replace('/', '\\').strip()
	return tempPath


def winFilePath(message):
	tempPath = filedialog.askopenfilename(title=message, parent=root).replace('/', '\\').strip()
	return tempPath


def winFilesPath(message):
	tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
	for i in range(len(tempPaths)):
		tempPaths[i] = tempPaths[i].replace('/', '\\')
	return tempPaths

class RacoonUtilitiesDirectoryError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


imagePath = winFilePath("Album cover")
audioPaths = winFilesPath("Audio files")

userChoice = input('Add author name to files?\nInput "n" if no, and an author name if yes.\n: ')
if userChoice != 'n':
	for index in range(len(audioPaths)):
		print(audioPaths[index])
		audioName = audioPaths[index][audioPaths[index].rfind("\\") + 1:]
		audioPath = audioPaths[index][:audioPaths[index].rfind("\\")]
		#sp.run(f'ren {audioPaths[index]} {userChoice}-{audioName}', shell=True)
		print(f'ren {audioPaths[index]} {userChoice}-{audioName}')
		audioPaths[index] = audioPaths[index][:audioPaths[index].rfind("\\") + 1] + userChoice + '-' + audioPaths[index][audioPaths[index].rfind("\\") + 1:]
		print(audioPaths[index])
