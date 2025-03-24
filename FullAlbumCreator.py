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


def makeVideo(image_input_path, sound_input_paths, output_path):
	if image_input_path == "" or sound_input_paths == "":
		raise RacoonUtilitiesMissingInputError("No input")

	if output_path == '':
		output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]

	if len(sound_input_paths) == 1:
		sound_input_paths = sound_input_paths[0]
		name = sound_input_paths[sound_input_paths.rfind('\\') + 1:sound_input_paths.rfind('.')]

		sp.run(
			f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{name}.mp4"',
			shell=True)
	else:
		names = []
		for INDEX in range(0, len(sound_input_paths)):
			names.append(sound_input_paths[INDEX][sound_input_paths[INDEX].rfind("\\"):sound_input_paths[INDEX].rfind(".")])
		print(names)

		for INDEX in range(len(names)):
			sp.run(
				f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths[INDEX]}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{names[INDEX]}.mp4"',
				shell=True)


def makeAlbum(image_input_path, sound_input_paths, final_filename, output_path):
	if image_input_path == "" or sound_input_paths == "" or final_filename == "":
		raise RacoonUtilitiesMissingInputError("No input")

	if output_path == '':
		output_path = sound_input_paths[0][:sound_input_paths[0].rfind("\\")]
	print(output_path)

	inputPath = ''
	for i in sound_input_paths:
		inputPath += f'-i "{i.replace('/', '\\')}" '
	print(inputPath)

	preConcat = ''
	for i in range(0, len(sound_input_paths)):
		preConcat += f'[{i}:a]'

	extension = sound_input_paths[0][sound_input_paths[0].rfind('.'):]

	sp.run(f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" "{output_path}\\output{extension}"', shell=True)
	sp.run(f'ren "{output_path}\\output{extension}" "{final_filename + extension}"', shell=True)

	sp.run(f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{output_path}\\{final_filename + extension}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{output_path}\\{final_filename}.mp4"', shell=True)


def askExit():
	input("Press enter to exit...")
	exit()


def mkFolder(path, folder_name):
	try:
		if sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True).returncode != 0:
			raise RacoonUtilitiesDirectoryError(f'Folder {folder_name} already exists')
	except RacoonUtilitiesDirectoryError:
		print(f'Folder {folder_name} already exists')
	else:
		sp.run(f'mkdir "{path}\\{folder_name}"', shell=True, capture_output=True)


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


def createFullAlbum(image_path, audio_paths, album_name):
	if image_path == "" or audio_paths == "" or album_name == "":
		raise RacoonUtilitiesMissingInputError("No input")

	directoryPath = audio_paths[0][:audio_paths[0].rfind("\\")]

	extensionList = []
	for audioFilePath in audio_paths:
		extensionList.append(audioFilePath[audioFilePath.rfind(".") + 1:])
	extensionList = list(dict.fromkeys(extensionList))

	if len(extensionList) > 1:
		audioFolder = "Audio"
	else:
		audioFolder = f'.{extensionList[0]}'

	mkFolder(directoryPath, audioFolder)
	mkFolder(directoryPath, ".mp4")

	makeVideo(image_path, audio_paths, f'{directoryPath}\\.mp4')
	makeAlbum(image_path, audio_paths, album_name, directoryPath)

	for songPath in audio_paths:
		sp.run(f'move "{songPath}" "{directoryPath}\\{audioFolder}"', shell=True)

	if image_path[image_path.rfind("\\")+1:] != f'{album_name}-cover{image_path[image_path.rfind("."):]}':
		sp.run(f'ren "{image_path}" "{album_name}-cover{image_path[image_path.rfind("."):]}"', shell=True)


if __name__ == "__main__":
	imagePath = winFilePath("Album cover")
	audioPaths = winFilesPath("Audio files")

	workingFolderPath = audioPaths[0][:audioPaths[0].rfind("\\")]
	workingFolderName = workingFolderPath[workingFolderPath.rfind("\\") + 1:]

	userChoice = input(f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
	if userChoice == '':
		albumName = workingFolderName
	else:
		albumName = userChoice

	userChoice = input('Add author name to files?\nInput "n" if no, and an author name if yes.\n: ')
	if userChoice != 'n':
		for index in range(len(audioPaths)):
			audioName = audioPaths[index][audioPaths[index].rfind("\\") + 1:]
			audioPath = audioPaths[index][:audioPaths[index].rfind("\\")]
			sp.run(f'ren {audioPaths[index]} {userChoice}-{audioName}', shell=True)
			audioPaths[index] = audioPaths[index][:audioPaths[index].rfind("\\") + 1] + userChoice + '-' + audioPaths[index][audioPaths[index].rfind("\\") + 1:]
		albumName = userChoice + '-' + albumName
	try:
		createFullAlbum(imagePath, audioPaths, albumName)
	except RacoonUtilitiesMissingInputError:
		print(f'No input / Wrong input')
		askExit()
	exit()
