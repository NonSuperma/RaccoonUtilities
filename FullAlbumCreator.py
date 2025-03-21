import subprocess as sp
from tkinter import filedialog, Tk

root = Tk()
root.lift()
root.withdraw()


class RacoonUtilitiesDirectoryError(Exception):
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
		if sp.run(f'mkdir {music_directory_path}\\{artist_name}\\{album_name}', shell=True,
				  capture_output=True).returncode != 0:
			raise RacoonUtilitiesDirectoryError("Directory already exists")
	except RacoonUtilitiesDirectoryError:
		print("Artist folder already exists")
	else:
		sp.run(f'mkdir "{music_directory_path}\\{artist_name}\\{album_name}"', shell=True, capture_output=True)


if __name__ == "__main__":
	imagePath = "C:\\Users\\tobia\\Music\\artworks-EEVoyxwjKDcOx4XL-CKrNWg-t1080x1080.jpg"
	audioPaths = "C:\\Users\\tobia\\Music\\1._Turned_Around.flac"
	albumName = "albumName"
	artistName = "artistName"
	musicDirectoryPath = "C:\\Users\\tobia\\Music"

	#sp.run(f'mkdir {musicDirectoryPath}\\{artistName}', shell=True)
	createFullAlbum(imagePath, audioPaths, albumName, artistName, musicDirectoryPath)
