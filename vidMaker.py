import subprocess as sp
from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE
from playsound3 import playsound
from colorama import init, Fore, Back, Style
from tkinter import Tk
import sys
import msvcrt
import time
import ctypes
import os


def resource_path(relative_path: str):
	base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))

	return os.path.join(base_path, relative_path)


if __name__ == "__main__":
	init(autoreset=True)
	try:
		imageInputPath = Ru.winFilePath("Album cover")
	except RuE.MissingInputError:
		Ru.askExit('No input image')

	try:
		soundInputPaths = Ru.winFilesPath("Audio files")
	except RuE.MissingInputError:
		Ru.askExit('No input sounds')

	outputPath = None
	vid = Ru(imageInputPath, soundInputPaths)
	print(f'{Fore.LIGHTCYAN_EX}[Converter]{Fore.RESET} Making video...')
	vid.makeVideo(outputPath, lenght_check=False, pure_audio=False	)
	print(f'{Fore.LIGHTCYAN_EX}[Converter]{Fore.RESET} Done!')
	#for path in soundInputPaths:
	#	sp.run(f'del "{path}"', shell=True)
	#sp.run(f'del "{imageInputPath}"', shell=True)



	sound_file = resource_path('au5-1.mp3')
	playsound(sound_file)
	sys.exit(0)

