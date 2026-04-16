from tkinter import filedialog, Tk
from pathlib import Path
from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.errors import *
import subprocess


def convert_file(file_path: Path, delete_old: bool = False): -> :


def convert_files(file_paths: list[Path], new_extension: str) -> None:
	file_count = len(file_paths)


	#single file path. Bare
	def convert(path_to_file: Path, newExtension):
		if path_to_file.suffix != new_extension:
			emptyName = Path.joinpath(path_to_file.parent, path_to_file.stem)
			extensions = ['.png', '.jpg', '.jpeg', '.webp', '.ico', '.gif', '.bmp', '.tiff', '.svg', '.heic', '.avif']
			print(path_to_file.suffix)
			if path_to_file.suffix in extensions:
				if newExtension == '.ico':
					dimentions = get_media_dimentions(path_to_file)
					print(dimentions)
					
					converted_file_name = path_to_file.name + '_cut'
					converted_file_path = path_to_file.parent / converted_file_name
					
					if dimentions[0] > 256 or dimentions[1] > 256:
						print(f'ffmpeg '
							   f'-y '
							   f'-i "{path_to_file}" '
							   f'-vf scale=256:256 '
							   f'"{converted_file_path}"')
						subprocess.run(f'ffmpeg '
							   f'-y '
							   f'-i "{path_to_file}" '
							   f'-vf scale=256:256 '
							   f'"{path_to_file}"',
							   shell=True, capture_output=True)
						subprocess.run(f'del "{path_to_file}"', shell=True)
						subprocess.run(
							f'ren "{path_to_file}" "{path_to_file[path_to_file.rfind('\\') + 1:]}"',
							shell=True)

				subprocess.run(f'ffmpeg '
					   f'-y '
					   f'-i "{path_to_file}" '
					   f'-update 1 '
					   f'-frames:v 1 '
					   f'"{emptyName}{newExtension}"',
					   shell=True)


			else:


				print(f'ffmpeg -i "{path_to_file}" -b:a {list(get_bitrate(path_to_file).values())[0]} "{emptyName}{newExtension}"')
				# subprocess.run(f'ffmpeg -i "{name}" -b:a {list(getBitrate(name).values())[0]} "{emptyName}{newExtension}"', shell=True)
				subprocess.run(f'ffmpeg -y -i "{path_to_file}" -b:a 270k "{emptyName}{newExtension}"',
					   shell=True)
		else:
			pass

	def convertDelete(name, newExtension):
		if name[name.rfind("."):] != new_extension:
			emptyName = name.replace(name[name.rfind("."):], "")
			subprocess.run(f'ffmpeg -i "{name}" -b:a 320k "{emptyName}{newExtension}"', shell=True)
			subprocess.run(f'del "{name}"', shell=True)
		else:
			pass

	if file_count > 1:
		a = input("1 - Keep all\n: ")
		if a == "1":
			for song in file_paths:
				convert(song, new_extension)
		elif a == "2":
			for song in file_paths:
				if input(f"\n\n\n\nKeep old {song} file? (y/n): ") == "n":
					convertDelete(song, new_extension)
				else:
					convert(song, new_extension)
		elif a == "3":
			for song in file_paths:
				convertDelete(song, new_extension)
	else:
		if input(f"Keep old file? (y/n): ") == "n":
			convertDelete(file_paths[0], new_extension)
		else:
			convert(file_paths[0], new_extension)


def main():
	track_paths = win_files_path()


if __name__ == '__main__':
	songs = win_files_path("Audio Files")
	convert_files(songs)