from tkinter import filedialog, Tk
from pathlib import Path
from Raccoon.windowsUtilities import *
from Raccoon.audioUtilities import *
from Raccoon.imageUtilities import *
from Raccoon.mediaUtilities import *
from Raccoon.miscUtilities import *
from Raccoon.errors import *
import subprocess
import playsound3

FFMPEG_PATH = str('ffmpeg.exe')


def convert_picture(file_path: Path, new_extension, delete_old: bool = False) -> Path | None:

	new_extension = new_extension.lower().strip()
	if '.' not in new_extension:
		new_extension = '.' + new_extension

	extensions = ['.png', '.jpg', '.jpeg', '.webp', '.ico', '.gif', '.bmp', '.tiff', '.svg', '.heic', '.avif']

	if new_extension not in extensions:
		return None

	if new_extension == '.ico':
		output_path = file_path.parent / file_path.with_suffix('.ico').name
		cmd = [FFMPEG_PATH, '-y',
			   '-v', 'error',
			   '-i', str(file_path),
			   '-vf', 'scale=256:256:force_original_aspect_ratio=decrease,pad=256:256:(ow-iw)/2:(oh-ih)/2',
			   str(output_path)
			   ]

		try:
			subprocess.run(cmd, check=True)
		except subprocess.CalledProcessError as e:
			ask_exit(e.stderr.decode('utf-8'))
		else:
			return output_path

	output_path = file_path.parent / file_path.with_suffix(new_extension).name

	cmd = [FFMPEG_PATH, '-y',
		   '-v', 'error',
		   '-i', str(file_path),
		   '-update', '1',
		   '-frames:v', '1',
		   str(output_path)
		   ]

	try:
		subprocess.run(cmd, check=True)
	except subprocess.CalledProcessError as e:
		ask_exit(e.stderr.decode('utf-8'))
	else:
		return output_path


def main():
	picture_path = win_file_path()
	convert_picture(picture_path, input(f'new extension: '))


if __name__ == '__main__':
	main()

	sound_path = get_bundled_file_path('au5-1.mp3')
	playsound3.playsound(str(sound_path))
