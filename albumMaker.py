from colorama import init, Fore, Back, Style
from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE
from playsound3 import playsound
from pathlib import Path
import subprocess as sp
import sys
import os


def resource_path(relative_path):

	try:
		base_path = sys._MEIPASS  # PyInstaller creates _MEIPASS temp dir
	except (Exception,):
		base_path = os.path.abspath(".")

	return os.path.join(base_path, relative_path)



if __name__ == "__main__":
	test = False
	if test:
		imageInputPath = Path('Test_Source\\clipboard__square.png')
	else:
		imageInputPath = Ru.winFilePath('Pick the album cover image')

	if test:
		soundInputPaths = [file for file in p.rglob("*.webp")]
	else:
		soundInputPaths = Ru.winFilesPath('Pick songs')

	workingFolderPath = soundInputPaths[0].parent
	workingFolderName = workingFolderPath.name

	if test:
		albumName = 'TEST'
	else:
		userChoice = input(
			f'{Fore.CYAN}[Info]{Fore.RESET} The selected songs are in a folder called {Fore.GREEN}"{workingFolderName}"{Fore.RESET}\n'
			f'Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n: '
		)

		if userChoice == '':
			albumName = workingFolderName

		else:
			albumName = userChoice

	outputPath = None

	album = Ru(imageInputPath, soundInputPaths)
	album.makeAlbum(outputPath, albumName)

	sound_file = str(resource_path('au5-1.mp3'))
	playsound(sound_file)

	sys.exit(0)
