import subprocess as sp
from tkinter import filedialog, Tk
from racoon import RaccoonErrors as RuE
from racoon import RaccoonMediaTools as Ru
from pathlib import Path


def convertFiles(songs: list[str]):
	songsCount = len(songs)

	extension = "." + input('Extension (without ".")\n: ')

	#single file path. Bare
	def convert(path_to_file: Path, newExtension):
		if path_to_file.suffix != extension:
			emptyName = Path.joinpath(path_to_file.parent, path_to_file.stem)
			extensions = ['.png', '.jpg', '.jpeg', '.webp', '.ico', '.gif', '.bmp', '.tiff', '.svg', '.heic', '.avif']
			print(path_to_file.suffix)
			if path_to_file.suffix in extensions:
				if newExtension == '.ico':
					dimentions = Ru.get_media_dimentions(path_to_file)
					print(dimentions)
					print(f'"{path_to_file[:path_to_file.rfind(".")]}_cut{path_to_file[path_to_file.rfind("."):]}"')

					if dimentions[0] > 256 or dimentions[1] > 256:
						print(f'ffmpeg '
							   f'-y '
							   f'-i "{path_to_file}" '
							   f'-vf scale=256:256 '
							   f'"{path_to_file[:path_to_file.rfind(".")]}_cut{path_to_file[path_to_file.rfind("."):]}"')
						sp.run(f'ffmpeg '
							   f'-y '
							   f'-i "{path_to_file}" '
							   f'-vf scale=256:256 '
							   f'"{path_to_file[:path_to_file.rfind(".")]}_cut{path_to_file[path_to_file.rfind("."):]}"',
							   shell=True, capture_output=True)
						sp.run(f'del "{path_to_file}"', shell=True)
						sp.run(
							f'ren "{path_to_file[:path_to_file.rfind(".")]}_cut{path_to_file[path_to_file.rfind("."):]}" "{path_to_file[path_to_file.rfind('\\') + 1:]}"',
							shell=True)

				sp.run(f'ffmpeg '
					   f'-y '
					   f'-i "{path_to_file}" '
					   f'-update 1 '
					   f'-frames:v 1 '
					   f'"{emptyName}{newExtension}"',
					   shell=True)


			else:


				print(f'ffmpeg -i "{path_to_file}" -b:a {list(Ru.get_bitrate(path_to_file).values())[0]} "{emptyName}{newExtension}"')
				# sp.run(f'ffmpeg -i "{name}" -b:a {list(Ru.getBitrate(name).values())[0]} "{emptyName}{newExtension}"', shell=True)
				sp.run(f'ffmpeg -y -i "{path_to_file}" -b:a 270k "{emptyName}{newExtension}"',
					   shell=True)
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