from Raccoon.errors import *
from pathlib import Path
from tkinter import filedialog, Tk
import time
import msvcrt
import sys



def askExit(message: str, timeout: int = 5) -> None:
	print(message)
	print(f'Press any key to exit (or wait {timeout} more seconds)')
	start = time.monotonic()
	last_shown = None

	while True:
		if msvcrt.kbhit():
			msvcrt.getch()
			break

		elapsed = time.monotonic() - start
		remaining = max(0, int(timeout - elapsed))

		if remaining != last_shown:

			print(f"\033[F\033[K"  # Move curson up, to beginning of line and clear line
				  f"Press any key to exit "
				  f"(or wait {remaining} more seconds)…")
			last_shown = remaining

		if elapsed >= timeout:
			break

		time.sleep(0.05)

	sys.exit()


def winDirPath(message: str = '') -> Path:
	root = Tk()
	root.withdraw()
	root.lift()

	file_path = Path(filedialog.askdirectory(title=message, parent=root))
	if not file_path:
		raise MissingInputError('User closed the window')

	return file_path


def winFilePath(message: str = '', filetypes=None, initialDir: Path = None) -> Path:
	root = Tk()
	root.lift()
	root.withdraw()

	kwargs = {"title": message, "parent": root}

	if filetypes is not None:
		if filetypes == 'audio':
			selection = [
				("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
				("MP3 files", "*.MP3"),
				("AAC files", "*.AAC"),
				("FLAC files", "*.FLAC"),
				("WAV files", "*.WAV"),
				("PCM files", "*.PCM"),
				("M4A files", "*.M4A"),
				("OPUS files", "*.opus"),
			]

			kwargs["filetypes"] = selection  # type: ignore[arg-type]
		elif filetypes == 'image':
			selection = [
				("Image files", "*.PNG *.JPEG *.jpg"),
				("PNG files", "*.PNG"),
				("JPEG files", "*.JPEG"),
				("JPG files", "*.jpg")
			]
			kwargs["filetypes"] = selection  # type: ignore[arg-type]
		else:
			kwargs["filetypes"] = filetypes

	if initialDir is not None:
		kwargs["initialdir"] = str(initialDir)
	file_path_str = filedialog.askopenfilename(**kwargs)  # type: ignore[arg-type]
	file_path = Path(file_path_str)

	if not file_path_str:
		raise MissingInputError('User closed the window')

	return file_path


def winFilesPath(message: str = '', filetypes=None, initialDir: Path = None) -> list[Path]:
	root = Tk()
	root.lift()
	root.withdraw()
	kwargs = {"title": message, "parent": root}
	if filetypes is not None:
		if filetypes == 'audio':
			selection = [
				("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
				("MP3 files", "*.MP3"),
				("AAC files", "*.AAC"),
				("FLAC files", "*.FLAC"),
				("WAV files", "*.WAV"),
				("PCM files", "*.PCM"),
				("M4A files", "*.M4A"),
				("OPUS files", "*.opus"),
			]
			kwargs["filetypes"] = selection  # type: ignore[arg-type]
		elif filetypes == 'image':
			selection = cast(Sequence[Tuple[str, str]],
							 [
								 ("Image files", "*.PNG *.JPEG"),
								 ("PNG files", "*.PNG"),
								 ("JPEG files", "*.JPEG")
							 ])
			kwargs["filetypes"] = selection  # type: ignore[arg-type]
		else:
			kwargs["filetypes"] = filetypes  # type: ignore[arg-type]

	if initialDir is not None:
		kwargs["initialdir"] = str(initialDir)

	file_paths = root.tk.splitlist(
		filedialog.askopenfilenames(**kwargs)  # type: ignore[arg-type]
	)
	root.destroy()

	if not file_paths:
		raise MissingInputError("User closed the window")

	return [Path(p) for p in file_paths]


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


def fileIsInDir(file_name: str, dir_path: Path) -> bool:
	if any(x.name == file_name for x in list(dir_path.iterdir())):
		return True
	else:
		return False
