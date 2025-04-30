import subprocess as sp
from tkinter import filedialog, Tk
from colorama import init, Fore, Back, Style
import os
import msvcrt
import time
import sys
from pathlib import Path


class RacoonErrors:
	class MissingInputError(Exception):
		def __init__(self, message):
			self.message = message
			super().__init__(self.message)

	class DirectoryError(Exception):
		def __init__(self, message):
			self.message = message
			super().__init__(self.message)


class RacoonMediaTools:

	def __init__(self, image_input_path: Path, sound_input_paths: list[Path]):
		self.image_input_path = image_input_path
		self.sound_input_paths = sound_input_paths

	@staticmethod
	def askExit(message: str) -> None:
		print(message)
		print("Press any key to exit...")

		start_time = time.time()
		while True:
			if msvcrt.kbhit() or time.time() - start_time > 5:
				break
			time.sleep(1)
		sys.exit()

	@staticmethod
	def mkFolder(path: Path, folder_name: str) -> None:
		if Path.exists(path):
			pass

		os.makedirs(Path.joinpath(path, folder_name), exist_ok=True)

	@staticmethod
	def winDirPath(message: str) -> Path:
		root = Tk()
		root.withdraw()
		root.lift()

		file_path = Path(filedialog.askdirectory(title=message, parent=root))
		if not file_path:
			raise RacoonErrors.MissingInputError('User closed the window')

		return file_path

	@staticmethod
	def winFilePath(message: str) -> Path:
		root = Tk()
		root.lift()
		root.withdraw()
		file_path = Path(filedialog.askopenfilename(title=message, parent=root))
		if not file_path:
			raise RacoonErrors.MissingInputError('User closed the window')

		return file_path

	@staticmethod
	def winFilesPath(message: str) -> list[Path]:
		root = Tk()
		root.lift()
		root.withdraw()
		file_paths = list(filedialog.askopenfilenames(title=message, parent=root))

		if not file_paths:
			raise RacoonErrors.MissingInputError('User closed the window')

		path_objects = [Path(p) for p in file_paths]
		return path_objects

	@staticmethod
	def getBitrate(sound_input_path: Path) -> dict[str, int] or None:
		if sound_input_path is list:
			sound_input_path = sound_input_path[0]

		extensions = ['png', 'jpg', 'jpeg', 'webp']
		if sound_input_path.suffix in extensions:
			return None

		value = sp.run(
			f'ffprobe '
			f'-v quiet '
			f'-select_streams a:0 '
			f'-show_entries stream=bit_rate '
			f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
			shell=True, capture_output=True).stdout.decode().strip()
		_type = 'bitrate'
		if value == 'N/A':
			value = sp.run(
				f'ffprobe '
				f'-v quiet '
				f'-select_streams a:0 '
				f'-show_entries stream=sample_rate '
				f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
				shell=True, capture_output=True).stdout.decode().strip()
			_type = 'samplerate'

		output = {
			_type: int(value)
		}
		return output

	@staticmethod
	def getAudioEncoding(file_path: Path) -> str or None:
		if isinstance(file_path, list):
			file_path = file_path[0]
		extensions = ['.png', '.jpg', '.jpeg', '.webp']
		if file_path.suffix in extensions:
			return None

		ffprobeOutput = sp.run(
			f'ffprobe -select_streams a:0 -show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 "{file_path}"',
			shell=True, capture_output=True)
		return ffprobeOutput.stdout.decode().strip()

	@staticmethod
	def getAudioDuration(file_path: Path) -> float or None:
		ffprobeOutput = sp.run(
			f'ffprobe -sexagesimal -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"',
			shell=True, capture_output=True)
		if ffprobeOutput.returncode != 0:
			print(ffprobeOutput.stdout.decode())
			return None
		else:
			return ffprobeOutput.stdout.decode().strip()

	@staticmethod
	def count_open_windows(process_name: str) -> int or None:
		import psutil
		import pygetwindow as gw
		import win32gui
		import win32process
		open_windows = 0

		for window in gw.getAllWindows():
			hwnd = window.handle

			if not win32gui.IsWindowVisible(hwnd):
				continue

			cls = win32gui.GetClassName(hwnd)
			if cls not in ("CabinetWClass", "ExploreWClass"):
				continue

			_, pid = win32process.GetWindowThreadProcessId(hwnd)

			try:
				proc = psutil.Process(pid)
				if proc.name().lower() == process_name:
					open_windows += 1
			except (psutil.NoSuchProcess, psutil.AccessDenied):
				pass

		return open_windows

	@staticmethod
	def get_media_dimentions(file_path) -> list[str] or None:
		ffprobeOutput = sp.run(
			f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 {file_path}',
			shell=True, capture_output=True)
		if ffprobeOutput.returncode != 0:
			return None
		else:
			dimentions = ffprobeOutput.stdout.decode().strip().split('x')
			dimentions = [int(dimention) for dimention in dimentions]
		return dimentions

	def makeVideo(self, output_path: Path or None, lenght_check):
		init(autoreset=True)
		image_input_path = self.image_input_path
		if image_input_path == "":
			raise RacoonErrors.MissingInputError("No album cover selected")
		sound_input_paths: list[Path] = self.sound_input_paths
		if sound_input_paths == "":
			raise RacoonErrors.MissingInputError("No audio/s selected")

		if output_path is None:
			output_path = sound_input_paths[0].parent

		if len(sound_input_paths) == 1:
			sound_input_paths: Path = Path(sound_input_paths[0])
			name = sound_input_paths.stem

			encoding = RacoonMediaTools.getAudioEncoding(sound_input_paths)

			if encoding == 'opus':
				print(f'{Fore.LIGHTCYAN_EX}[Info]{Fore.RESET} Keeping Opus as encoder')
				ffmpegOutput = sp.run(f'ffmpeg '
									  # f'-loglevel fatal '
									  f'-y '
									  f'-stream_loop -1 '
									  f'-framerate 1 '
									  f'-i "{image_input_path}" '
									  f'-i "{sound_input_paths}" '
									  f'-c:v libx264 '
									  f'-tune stillimage '
									  f'-c:a copy '
									  f'-shortest '
									  f'-movflags +faststart '
									  f'-vf "format=yuv420p" '
									  f'-r 1 '
									  f'"{output_path}\\{name}.mp4"',
									  shell=True, capture_output=False)

			else:
				ffmpegOutput = sp.run(f'ffmpeg '
									  # f'-loglevel fatal '
									  f'-y '
									  f'-stream_loop -1 '
									  f'-framerate 1 '
									  f'-i "{image_input_path}" '
									  f'-i "{sound_input_paths}" '
									  f'-c:v libx264 '
									  f'-tune stillimage '
									  f'-c:a opus '
									  f'-shortest '
									  f'-movflags +faststart '
									  f'-vf "format=yuv420p" '
									  f'-r 1 '
									  f'"{output_path}\\{name}.mp4"',
									  shell=True, capture_output=False)
			if lenght_check:
				oryginalDuration = RacoonMediaTools.getAudioDuration(sound_input_paths)
				converterDuration = RacoonMediaTools.getAudioDuration(Path(f'{output_path}\\{name}.mp4'))
				if oryginalDuration != converterDuration:
					temp_path = sound_input_paths.stem + "_temp" + sound_input_paths.suffix
					sp.run(f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_paths}" -c copy "{temp_path}"',
						   shell=True)
					os.replace(temp_path, sound_input_paths)
			return ffmpegOutput

		else:
			names = []
			for INDEX in range(0, len(sound_input_paths)):
				names.append(sound_input_paths[INDEX].stem)

			for INDEX in range(len(names)):
				ffmpegOutput = []
				ffmpegOutputPart = sp.run(
					f'ffmpeg '
					f'-y '
					# f'-loglevel warning '
					f'-loop 1 '
					f'-i "{image_input_path}" '
					f'-i "{sound_input_paths[INDEX]}" '
					f'-c:v libx264 '
					f'-tune stillimage '
					f'-c:a opus '
					f'-b:a 256k '
					f'-shortest '
					f'-movflags +faststart '
					f'-vf "format=yuv420p" '
					f'-r 30 '
					f'"{Path.joinpath(output_path, names[INDEX], '.mp4')}"',
					shell=True)

				if lenght_check:
					oryginalDuration = RacoonMediaTools.getAudioDuration(sound_input_paths[INDEX])
					converterDuration = RacoonMediaTools.getAudioDuration(Path.joinpath(output_path, names[INDEX], '.mp4'))

					if oryginalDuration != converterDuration:
						temp_path = sound_input_paths[INDEX].stem + "_temp" + sound_input_paths[INDEX].suffix
						sp.run(
							f'ffmpeg -y -ss 00:00:00 -to {oryginalDuration} -i "{sound_input_paths[INDEX]}" -c copy "{temp_path}"',
							shell=True)
						os.replace(temp_path, sound_input_paths[INDEX])
					ffmpegOutput.append(ffmpegOutputPart)

			return ffmpegOutput

	def makeAlbum(self, output_path: str or None, final_filename: str):
		init(autoreset=True)

		image_input_path = self.image_input_path
		if image_input_path == "":
			raise RacoonErrors.MissingInputError("No album cover selected")
		sound_input_paths = self.sound_input_paths
		if sound_input_paths == '':
			raise RacoonErrors.MissingInputError("No audio/s selected")
		if final_filename == '':
			raise RacoonErrors.MissingInputError("No final filename provided")

		if output_path is None:
			output_path = sound_input_paths[0].parent

		inputPath = ''
		for path in sound_input_paths:
			inputPath += f'-i "{path}" '

		preConcat = ''
		for i in range(0, len(sound_input_paths)):
			preConcat += f'[{i}:a]'

		extension = sound_input_paths[0].suffix

		sp.run(f'ffmpeg '
			   f'-y '
			   f'{inputPath}'  # No space here on purpose
			   f'-filter_complex "{preConcat}concat=n={len(sound_input_paths)}:v=0:a=1" '
			   f'-b:a 256k '
			   f'"{output_path}\\{final_filename + extension}"',
			   shell=True)

		print(image_input_path, [(Path(f'{output_path}\\{final_filename + extension}'))])
		tempVid = RacoonMediaTools(image_input_path, [(Path(f'{output_path}\\{final_filename + extension}'))])
		tempVid.makeVideo(output_path, lenght_check=False)
