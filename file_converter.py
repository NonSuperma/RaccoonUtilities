import subprocess as sp
from tkinter import filedialog, Tk
from Racoon import RacoonErrors as RuE
from Racoon import RacoonMediaTools as Ru



def convertFiles(songs: list[str]):
	songsCount = len(songs)

	extension = "." + input('Extension (without ".")\n: ')

	def convert(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name[:name.rfind(".")]
			bitrate = Ru.getBitrate(name)

			if bitrate is None:
				if newExtension == '.ico':
					dimentions = Ru.get_media_dimentions(name)
					print(dimentions)
					print(f'"{name[:name.rfind(".")]}_cut{name[name.rfind("."):]}"')

					if dimentions[0] > 256 or dimentions[1] > 256:
						print(f'ffmpeg '
							   f'-y '
							   f'-i "{name}" '
							   f'-vf scale=256:256 '
							   f'"{name[:name.rfind(".")]}_cut{name[name.rfind("."):]}"')
						sp.run(f'ffmpeg '
							   f'-y '
							   f'-i "{name}" '
							   f'-vf scale=256:256 '
							   f'"{name[:name.rfind(".")]}_cut{name[name.rfind("."):]}"',
							   shell=True, capture_output=True)
						sp.run(f'del "{name}"', shell=True)
						sp.run(
							f'ren "{name[:name.rfind(".")]}_cut{name[name.rfind("."):]}" "{name[name.rfind('\\') + 1:]}"',
							shell=True)

				sp.run(f'ffmpeg '
					   f'-y '
					   f'-i "{name}" '
					   f'-update 1 '
					   f'-frames:v 1 '
					   f'"{emptyName}{newExtension}"',
					   shell=True)


			else:


				print(f'ffmpeg -i "{name}" -b:a {list(Ru.getBitrate(name).values())[0]} "{emptyName}{newExtension}"')
				sp.run(f'ffmpeg -i "{name}" -b:a {list(Ru.getBitrate(name).values())[0]} "{emptyName}{newExtension}"', shell=True)
		else:
			pass

	def convertDelete(name, newExtension):
		if name[name.rfind("."):] != extension:
			emptyName = name.replace(name[name.rfind("."):], "")
			sp.run(f'ffmpeg -i "{name}" -b:a 320k "{emptyName}{newExtension}"', shell=True)
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