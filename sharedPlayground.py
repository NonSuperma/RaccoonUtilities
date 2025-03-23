import subprocess as sp
from tkinter import filedialog, Tk


class RacoonUtilitiesMissingInputError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


class RacoonUtilitiesDirectoryError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


class RacoonUtilitiesInputLengthError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


def askExit():
	input("Press enter to exit...")
	exit()


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



#imagePath = winFilePath("Album cover")
#audioPaths = winFilesPath("Audio files")
vidPath = 'C:\\Users\\tobia\\Downloads\\tropical_tech_house_mix_vol._3.mp4'


#sp.run(f'ffplay -i {vidPath} -vf "crop=1132:1080:395:0"', shell=True)
#print(vidPath[:vidPath.rfind('.')] + '__CUT__' + vidPath[vidPath.rfind('.'):])
sp.run(f'ffmpeg -i {vidPath} -acodec copy -vf "crop=1132:1080:395:0" {vidPath[:vidPath.rfind('.')] + '__CROPPED__' + vidPath[vidPath.rfind('.'):]}', shell=True)
