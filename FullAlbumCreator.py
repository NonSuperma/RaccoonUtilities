import subprocess as sp
from tkinter import filedialog, Tk
from racoon import RaccoonMediaTools as RacoonMT
from racoon import RaccoonErrors as RuE
from racoon import RacoonWindowsTools as RacoonWT


def createFullAlbum(image_path, audio_paths, album_name):
	if image_path == "" or audio_paths == "" or album_name == "":
		raise RuE.MissingInputError("No input")

	directoryPath = audio_paths[0][:audio_paths[0].rfind("\\")]

	extensionList = []
	for audioFilePath in audio_paths:
		extensionList.append(audioFilePath[audioFilePath.rfind(".") + 1:])
	extensionList = list(dict.fromkeys(extensionList))

	if len(extensionList) > 1:
		audioFolder = "Audio"
	else:
		audioFolder = f'.{extensionList[0]}'

	RacoonWT.mkFolder(directoryPath, audioFolder)
	RacoonWT.mkFolder(directoryPath, ".mp4")

	albumData = RacoonMT(image_path, audio_paths)
	# albumData.makeVideo(f'{directoryPath}\\.mp4')
	albumData.make_album(directoryPath, album_name)

	for songPath in audio_paths:
		sp.run(f'move "{songPath}" "{directoryPath}\\{audioFolder}"', shell=True)

	if image_path[image_path.rfind("\\")+1:] != f'{album_name}-cover{image_path[image_path.rfind("."):]}':
		sp.run(f'ren "{image_path}" "{album_name}-cover{image_path[image_path.rfind("."):]}"', shell=True)


if __name__ == "__main__":
	imagePath = RacoonWT.winFilePath("Album cover")
	audioPaths = RacoonWT.winFilesPath("Audio files")

	workingFolderPath = audioPaths[0][:audioPaths[0].rfind("\\")]
	workingFolderName = workingFolderPath[workingFolderPath.rfind("\\") + 1:]

	userChoice = input(f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
	if userChoice == '':
		albumName = workingFolderName
	else:
		albumName = userChoice

	userChoice = input('Add author name to files?\nPress enter if no, or input an author name if yes.\n: ')
	if userChoice != '':
		for index in range(len(audioPaths)):
			audioName = audioPaths[index][audioPaths[index].rfind("\\") + 1:]
			audioPath = audioPaths[index][:audioPaths[index].rfind("\\")]
			sp.run(f'ren {audioPaths[index]} {userChoice}-{audioName}', shell=True)
			audioPaths[index] = audioPaths[index][:audioPaths[index].rfind("\\") + 1] + userChoice + '-' + audioPaths[index][audioPaths[index].rfind("\\") + 1:]
		albumName = userChoice + '-' + albumName
	try:
		createFullAlbum(imagePath, audioPaths, albumName)
	except RuE.MissingInputError:
		print(f'No input / Wrong input')
		askExit()
	exit()
