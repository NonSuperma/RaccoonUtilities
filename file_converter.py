import subprocess as sp
from tkinter import filedialog, Tk
from Racoon import RacoonErrors as RuE
from Racoon import RacoonMediaTools as Ru



def convertFiles(songs: list):
	songsCount = len(songs)

	extension = "." + input("Extension: ")

	def convert(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name[:name.rfind("\\")+1]
			sp.run(f'ffmpeg -i "{name}" -b:a 320k "{emptyName}{newExtension}"', shell=True)
		else:
			pass

	def convertDelete(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name.replace(name[name.rfind("."):], "")
			sp.run(f'ffmpeg -i "{name}" "{emptyName}{newExtension}"', shell=True)
			sp.run(f'del "{name}"', shell=True)
		else:
			pass

	if songsCount > 1:
		a = input("1 - Keep all\n2 - Choose for each\n3 - Delete all\n: ")
		if a == "1":
			for song in songs:
				convert(song, extension)
		elif a == "2":
			for song in songs:
				if input(f"\n\n\n\nKeep old {song} file? (y/n): ") == "n":
					convertDelete(song, extension)
				else:
					convert(song, extension)
		elif a == "3":
			for song in songs:
				convertDelete(song, extension)
	else:
		if input(f"Keep old file? (y/n): ") == "n":
			convertDelete(songs[0], extension)
		else:
			convert(songs[0], extension)

if __name__ == '__main__':
	songs = Ru.winFilesPath("Audio Files")
	convertFiles(songs)