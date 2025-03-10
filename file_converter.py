import subprocess as sp
import tkinter.filedialog

songs = []
for song in tkinter.filedialog.askopenfilenames():
	songs.append(song)

songsCount = 0
for i in songs:
	if i.find(songs[0][0:2]) != -1:
		songsCount += 1

print(songs)
print(songsCount)

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
			if input(f"\n\n\n\nKeep old {song} file? y/n: ") == "n":
				convertDelete(song, extension)
			else:
				convert(song, extension)
	elif a == "3":
		for song in songs:
			convertDelete(song, extension)
else:
	if input(f"Keep old file? y/n: ") == "n":
		convertDelete(songs[0], extension)
	else:
		convert(songs[0], extension)
