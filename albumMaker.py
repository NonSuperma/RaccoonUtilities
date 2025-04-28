import subprocess as sp
from Racoon import RacoonMediaTools as Ru
from Racoon import RacoonErrors as RuE
from playsound3 import playsound
from tkinter import Tk
import sys
import msvcrt
import time
import ctypes
import os


def resource_path(relative_path):

	try:
		base_path = sys._MEIPASS  # PyInstaller creates _MEIPASS temp dir
	except (Exception,):
		base_path = os.path.abspath(".")

	return os.path.join(base_path, relative_path)


def show_console():
	root = Tk()
	root.withdraw()
	root.lift()
	ctypes.windll.kernel32.AllocConsole()
	sys.stdout = open('CONOUT$', 'w')
	sys.stderr = open('CONOUT$', 'w')
	sys.stdin = open('CONIN$', 'r')


def hide_console():
	ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)


if __name__ == "__main__":
	imageInputPath = Ru.winFilePath('Pick the album cover image')
	soundInputPaths = Ru.winFilesPath('Pick songs')

	workingFolderPath = soundInputPaths[0][:soundInputPaths[0].rfind("\\")]
	workingFolderName = workingFolderPath[workingFolderPath.rfind("\\") + 1:]
	show_console()
	userChoice = input(
		f'The selected songs are in a folder called "{workingFolderName}"\nPress enter to use that folder as the album name, or input the album name manually\n: ')
	if userChoice == '':
		albumName = workingFolderName
	else:
		albumName = userChoice

	outputPath = None

	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeAlbum(outputPath, albumName)

	except RuE.MissingInputError:
		show_console()
		print("No input!")
		input("Press enter to exit...")
		sys.exit()
	except (Exception,):
		show_console()
		input("Press enter to exit...")
		sys.exit()

	sound_file = resource_path('au5-1.mp3')
	playsound(sound_file)

	sys.exit(0)
