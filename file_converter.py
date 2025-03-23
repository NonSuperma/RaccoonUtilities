import subprocess as sp
from tkinter import filedialog, Tk


def winFilePath(message):
	root = Tk()
	root.lift()
	root.withdraw()
	tempPath = filedialog.askopenfilename(title=message, parent=root).replace('/', '\\').strip()
	return tempPath


def winFilesPath(message):
	root = Tk()
	root.lift()
	root.withdraw()
	tempPaths = list(filedialog.askopenfilenames(title=message, parent=root))
	for i in range(len(tempPaths)):
		tempPaths[i] = tempPaths[i].replace('/', '\\')
	return tempPaths


def convertFiles(songs):
	songsCount = 0
	for i in songs:
		if i.find(songs[0][0:2]) != -1:
			songsCount += 1

	extension = "." + input("Extension: ")

	def convert(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name.replace(name[name.rfind("."):], "")
			sp.run("ffmpeg -i " + name + " " + emptyName + newExtension, shell=True)
		else:
			pass

	def convertDelete(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name.replace(name[name.rfind("."):], "")
			sp.run(f"ffmpeg -i {name} {emptyName}{newExtension}", shell=True)
			sp.run("del " + name.replace("/", "\\"), shell=True)
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
	songs = winFilesPath("Audio Files")
	convertFiles(songs)