import subprocess as sp
import tkinter.filedialog


class RacoonUtilitiesMissingInputError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


def askExit():
	input("Press enter to exit...")
	exit()


def makeVideo(image_input_path, sound_input_paths):
	if image_input_path == "" or sound_input_paths == "":
		raise RacoonUtilitiesMissingInputError("No input")
	if len(sound_input_paths) == 1:
		sound_input_paths = sound_input_paths[0]
		name = sound_input_paths[:sound_input_paths.rfind(".")]

		sp.run(f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{name}.mp4"', shell=True)
		sp.run(f'del "{image_input_path.replace('/', '\\')}"', shell=True)
		sp.run(f'del "{sound_input_paths.replace('/', '\\')}"', shell=True)

	else:
		names = []
		for number in range(0, len(sound_input_paths)):
			names.append(sound_input_paths[number][:sound_input_paths[number].rfind(".")])
		print(names)

		for index in range(len(names)):
			sp.run(f'ffmpeg -r 1 -loop 1 -i "{image_input_path}" -i "{sound_input_paths[index]}" -c:v libx264 -acodec copy -r 1 -shortest -vf format=yuv420p "{names[index]}.mp4"', shell=True)
			sp.run(f'del "{sound_input_paths[index].replace('/', '\\')}"', shell=True)
		sp.run(f'del "{image_input_path.replace('/', '\\')}"', shell=True)


if __name__ == "__main__":
	imageInputPath = tkinter.filedialog.askopenfilename()
	soundInputPaths = tkinter.filedialog.askopenfilenames()

	try:
		makeVideo(imageInputPath, soundInputPaths)
	except RacoonUtilitiesMissingInputError:
		print("No input")
		askExit()
