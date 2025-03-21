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


music_directory_path = "C:\\Users\\tobia\\Music"
artist_name = "Mark"


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
		for index in range(0, len(sound_input_paths)):
			names.append(sound_input_paths[index][:sound_input_paths[index].rfind(".")])
		print(names)

		for index in range(len(names)):
			sp.run(
				f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths[index]}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{names[index]}.mp4"',
				shell=True)


if __name__ == "__main__":
	imageInputPath = winFilePath()
	soundInputPaths = winFilesPath()
	outputPath = ''
	try:
		makeVideo(imageInputPath, soundInputPaths, outputPath)
	except RacoonUtilitiesMissingInputError:
		print("No input!")
		askExit()

exit()
