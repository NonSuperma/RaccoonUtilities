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
		try:
			imageInputPath = Ru.winFilePath('Pick the album cover image', filetypes='image')
		except RuE.MissingInputError:
			Ru.askExit("User closed the window")

	if test:
		soundInputPaths = [file for file in p.rglob("*.webp")]
	else:
		try:
			selection = [
					 ("All without images", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus *.webm *.mp4 *.mov *.avi *.wmv"),
					 ("MP3 files", "*.MP3"),
					 ("AAC files", "*.AAC"),
					 ("FLAC files", "*.FLAC"),
					 ("WAV files", "*.WAV"),
					 ("PCM files", "*.PCM"),
					 ("M4A files", "*.M4A"),
					 ("OPUS files", "*.opus"),
					 ("Video files", "*.webm *.mp4 *.mov *.avi *.wmv")
			]
			soundInputPaths = Ru.winFilesPath('Pick songs', filetypes=selection)
		except RuE.MissingInputError:
			Ru.askExit("User closed the window")

	workingFolderPath = soundInputPaths[0].parent
	workingFolderName = workingFolderPath.name

	if test:
		albumName = 'TEST'
	else:
		userChoice = input(
			f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} The selected songs are in a folder called {Fore.GREEN}"{workingFolderName}"{Fore.RESET}\n'
			f'       Press {Back.BLACK}ENTER{Back.RESET} to use that folder as the album name, or input the album name manually\n'
			f'       "[]" gets converted into {Fore.GREEN}"{workingFolderName}"{Fore.RESET} no matter where it is in the input: \n'
			f'       '
		)

		if userChoice == '':
			albumName = workingFolderName + ' [Full Album]'

		else:
			albumName = userChoice + ' [Full Album]'
			if albumName.find('[]') != -1:
				albumName = albumName.replace('[]', workingFolderName)
			print(f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} Name chosen: {Fore.LIGHTBLUE_EX}"{albumName}"{Fore.RESET}')

	outputPath = None

	album = Ru(imageInputPath, soundInputPaths)
	album.makeAlbum(outputPath, albumName)

	sound_file = str(resource_path('au5-1.mp3'))
	playsound(sound_file)

	sys.exit(0)
