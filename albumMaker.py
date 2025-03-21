import subprocess as sp
import tkinter.filedialog


class RacoonUtilitiesInputLengthError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


class RacoonUtilitiesMissingInputError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


def askExit():
	input("Press enter to exit...")
	exit()


def makeAlbum(image_input_path, sound_input_paths, final_filename):
	if image_input_path == "" or sound_input_paths == "" or final_filename == "":
		raise RacoonUtilitiesMissingInputError("No input")

	directoryPath = sound_input_paths[0].replace('/', '\\')
	directoryPath = directoryPath[:directoryPath.rfind("\\")] + "\\"

	print(directoryPath)

	inputPath = ''
	for i in sound_input_paths:
		inputPath += f'-i "{i.replace('/', '\\')}" '

	preConcat = ''
	for i in range(0, len(sound_input_paths)):
		preConcat += f'[{i}:a]'

	extension = sound_input_paths[0][sound_input_paths[0].rfind('.'):]

	sp.run(
		f'ffmpeg {inputPath}-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" {directoryPath}output{extension}',
		shell=True)
	sp.run(f'ren "{directoryPath}output{extension}" "{final_filename + extension}"', shell=True)

	name = directoryPath + final_filename

	sp.run(
		f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{name + extension}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"',
		shell=True)
	if f'"{name}.mp4"' != f'{final_filename + extension}':
		sp.run(f'del {final_filename + extension}', shell=True)



if __name__ == "__main__":
	imageInputPath = tkinter.filedialog.askopenfilename()
	soundInputPaths = tkinter.filedialog.askopenfilenames()
	finalFilename = input("Final file name: ")
	try:
		makeAlbum(imageInputPath, soundInputPaths, finalFilename)
	except RacoonUtilitiesMissingInputError:
		print("RacoonUtilitiesMissingInputError: No input")
		askExit()
	except RacoonUtilitiesInputLengthError:
		print("RacoonUtilitiesInputLengthError: Too many audio files selected")
		askExit()
	exit()
