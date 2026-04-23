import subprocess as sp
import tkinter.filedialog
from tkinter import filedialog, Tk


class RacoonUtilitiesMissingInputError(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(self.message)


def winFilesPath(message):
	root = Tk()
	root.lift()
	root.withdraw()
	tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
	for i in range(len(tempPaths)):
		tempPaths[i] = tempPaths[i].replace('/', '\\')
	return tempPaths


def fixVideos(video_paths):
	if video_paths == []:
		raise RacoonUtilitiesMissingInputError("No input!")

	for INDEX in range(len(video_paths)):
		video_paths[INDEX] = video_paths[INDEX].replace('/', '\\')

	paths = []
	for file in video_paths:
		paths.append(file[:file.rfind("\\")])

	names = []
	for file in video_paths:
		names.append(file[file.rfind("\\")+1:file.rfind('.')])

	if len(video_paths) == 0:
		exit()

	for INDEX in range(len(video_paths)):
		sp.run(f'ffmpeg -i {video_paths[INDEX]} -c:v libx264 -crf 20 -c:a copy -b:a 160k -vf format=yuv420p -movflags +faststart {paths[INDEX]}\\{names[INDEX]}.fixed.mp4', shell=True)
		sp.run(f'del {paths[INDEX]}\\{names[INDEX]}.mp4', shell=True)
		sp.run(f'ren {paths[INDEX]}\\{names[INDEX]}.fixed.mp4 {names[INDEX]}.mp4', shell=True)


if __name__ == '__main__':
	try:
		videos = winFilesPath("Choose videos to fix")
		fixVideos(videos)
	except (RacoonUtilitiesMissingInputError, ):
		print("No input!")
