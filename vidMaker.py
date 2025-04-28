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
	imageInputPath = Ru.winFilePath("Album cover")
	soundInputPaths = Ru.winFilesPath("Audio files")
	outputPath = None
	try:
		vid = Ru(imageInputPath, soundInputPaths)
		vid.makeVideo(outputPath)
		#for path in soundInputPaths:
		#	sp.run(f'del "{path}"', shell=True)
		#sp.run(f'del "{imageInputPath}"', shell=True)

	except RuE.MissingInputError:
		show_console()
		print("No input!")
		print("Press any key to exit...")

		start_time = time.time()
		while True:
			if msvcrt.kbhit() or time.time() - start_time > 5:
				break
			time.sleep(1)
		sys.exit()
	except (Exception,):
		show_console()
		input("Press any key to exit...")
		sys.exit()
	sound_file = resource_path('au5-1.mp3')
	playsound(sound_file)
	sys.exit(0)
