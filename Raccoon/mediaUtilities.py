from pathlib import Path
import subprocess


def get_media_dimentions(file_path) -> list[int] | None:
	try:
		ffprobeOutput = subprocess.run(
			f'ffprobe '
			f'-v error '
			f'-select_streams v:0 '
			f'-show_entries stream=width,height -of csv=s=x:p=0 '
			f'"{file_path}"',
			shell=True, capture_output=True, text=True, check=True)
	except subprocess.CalledProcessError:
		return None
	else:
		dimentions = [int(dimention) for dimention in ffprobeOutput.stdout.strip().split('x')]
	return dimentions
