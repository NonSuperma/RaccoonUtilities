from os import makedirs
from pathlib import Path
import subprocess
from tkinter import filedialog, Tk

def get_duration(file_path):
	cmd = [
		'ffprobe',
		'-v', 'error',
		'-show_entries', 'format=duration',
		'-of', 'default=noprint_wrappers=1:nokey=1',
		str(file_path)
	]
	result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	return float(result.stdout.strip())


def win_files_path(message: str = '', filetypes=None, initialDir: Path = None) -> list[Path]:
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


def main():
	file_paths = win_files_path()
	for file_path in file_paths:
		print(f'Processing {file_path}...')

		makedirs(file_path.parent / 'mp4', exist_ok=True)
		
		subprocess.run(f'ffmpeg '
					   f'-y '
					   f'-r 1 '
					   f'-i "{file_path}" '
					   f'-map 0:v -map 0:a '
					   f'-c:v libx264 -crf 30 -tune stillimage '
					   f'-c:a libmp3lame '
					   f'-b:a 320k '
					   f'-pix_fmt yuv420p '
					   f'-vf "loop=-1:1:0,fps=10" '
					   f'-r 10 '
					   f'-t {get_duration(file_path)} '
					   f'-movflags +faststart '
					   f'-disposition:v:0 0 '
					   f'"{file_path.parent / 'mp4' / file_path.with_suffix(".mp4").name}"')
		print(f'Done!\n')


if __name__ == '__main__':
	main()