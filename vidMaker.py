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


def resource_path(relative_path):
	base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
	return Path.joinpath(base_path, relative_path)


def play_success_sound() -> None:
	sound_file = resource_path('au5-1.mp3')
	playsound(sound_file)


def main():
	init(autoreset=True)

	try:
		imageInputPath = Ru.winFilePath("Album cover")
	except RuE.MissingInputError:
		Ru.askExit(f'{Fore.RED}No input image!{Fore.RESET}')

	try:
		soundInputPaths = Ru.winFilesPath("Audio files")
	except RuE.MissingInputError:
		Ru.askExit(f'{Fore.RED}No input sounds!{Fore.RESET}')

	vid = Ru(imageInputPath, soundInputPaths)

	print(f'{Fore.LIGHTCYAN_EX}[Converter]{Fore.RESET} Making video...')
	vid.makeVideo()
	print(f'{Fore.LIGHTCYAN_EX}[Converter]{Fore.RESET} Done!')

	# for path in soundInputPaths:
	#	sp.run(f'del "{path}"', shell=True)
	# sp.run(f'del "{imageInputPath}"', shell=True)


if __name__ == "__main__":
	main()
	play_success_sound()
	sys.exit(0)
