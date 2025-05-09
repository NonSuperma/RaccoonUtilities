import subprocess as sp
from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE
from playsound3 import playsound
from pathlib import Path
import sys
import os


def resource_path(relative_path):

	try:
		base_path = sys._MEIPASS  # PyInstaller creates _MEIPASS temp dir
	except (Exception,):
		base_path = os.path.abspath(".")

	return os.path.join(base_path, relative_path)



if __name__ == "__main__":
	test = True
	if not test:
		imageInputPath = Ru.winFilePath('Pick the album cover image')
	else:
		imageInputPath = Path('C:\\Users\\tobia\\Downloads\\New folder\\cover.jpg')

	if test:
		soundInputPaths = [Path('C:/Users/tobia/Downloads/New folder/Stoned Jesus - Electric Mistress.opus'), Path("C:/Users/tobia/Downloads/New folder/Stoned Jesus - I'm The Mountain.opus"), Path('C:/Users/tobia/Downloads/New folder/Stoned Jesus - Indian.opus')]
	else:
		soundInputPaths = Ru.winFilesPath('Pick songs')

	workingFolderPath = soundInputPaths[0].parent
	workingFolderName = workingFolderPath.name
	if not test:
		userChoice = input(
			f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
		if userChoice == '':
			albumName = workingFolderName
		else:
			albumName = userChoice
	else:
		albumName = 'TEST'

	outputPath = None

	album = Ru(imageInputPath, soundInputPaths)
	album.makeAlbum(outputPath, albumName)



	sound_file = resource_path('au5-1.mp3')
	playsound(sound_file)

	sys.exit(0)
