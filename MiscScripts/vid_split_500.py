import subprocess
import math
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Sequence, Tuple, cast


class MissingInputError(Exception):
	pass


class FileSelector:
	@staticmethod
	def win_files_path(message: str = '', filetypes=None, initialDir: Path = None) -> list[Path]:
		root = Tk()
		root.attributes('-topmost', True)
		root.withdraw()
		kwargs = {"title": message, "parent": root}

		if filetypes is not None:
			if filetypes == 'audio':
				selection = [
					("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus *.ogg"),
					("MP3 files", "*.MP3"),
					("AAC files", "*.AAC"),
					("FLAC files", "*.FLAC"),
					("WAV files", "*.WAV"),
					("PCM files", "*.PCM"),
					("M4A files", "*.M4A"),
					("OPUS files", "*.opus"),
					("OGG files", "*.ogg"),
				]
				kwargs["filetypes"] = selection
			elif filetypes == 'image':
				selection = cast(Sequence[Tuple[str, str]],
								 [
									 ("Image files", "*.PNG *.JPEG"),
									 ("PNG files", "*.PNG"),
									 ("JPEG files", "*.JPEG")
								 ])
				kwargs["filetypes"] = selection
			elif filetypes == 'video':
				selection = [
					("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"),
					("All files", "*.*")
				]
				kwargs["filetypes"] = selection
			else:
				kwargs["filetypes"] = filetypes

		if initialDir is not None:
			kwargs["initialdir"] = str(initialDir)

		file_paths = root.tk.splitlist(
			filedialog.askopenfilenames(**kwargs)
		)
		root.destroy()

		if not file_paths:
			raise MissingInputError("User closed the window")

		return [Path(p) for p in file_paths]


class VideoMetadata:
	def __init__(self, file_path: Path):
		self.file_path = file_path
		self.size = file_path.stat().st_size
		self.duration = self._get_duration()

	def _get_duration(self) -> float:
		cmd = [
			"ffprobe",
			"-v", "error",
			"-show_entries", "format=duration",
			"-of", "default=noprint_wrappers=1:nokey=1",
			str(self.file_path)
		]
		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
		return float(result.stdout.strip())


class VideoSplitter:
	def __init__(self, target_size_mb: int = 480):
		self.target_size_bytes = target_size_mb * 1024 * 1024

	def split(self, metadata: VideoMetadata):
		if metadata.size <= self.target_size_bytes:
			print(f"File {metadata.file_path.name} is already under the target size.")
			return

		chunk_duration = math.floor((self.target_size_bytes / metadata.size) * metadata.duration)
		total_duration = metadata.duration
		current_start = 0.0
		part = 1

		print(f"Splitting {metadata.file_path.name}...")

		while current_start < total_duration:
			output_name = f"{metadata.file_path.stem}_part{part}{metadata.file_path.suffix}"
			output_path = metadata.file_path.parent / output_name

			cmd = [
				"ffmpeg",
				"-y",
				"-i", str(metadata.file_path),
				"-ss", str(current_start),
				"-t", str(chunk_duration),
				"-c", "copy",
				str(output_path)
			]

			subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
			print(f"Created {output_name}")

			current_start += chunk_duration
			part += 1


class Application:
	@staticmethod
	def run():
		try:
			files = FileSelector.win_files_path(message="Select video files to split", filetypes="video")
			splitter = VideoSplitter(target_size_mb=480)

			for file_path in files:
				metadata = VideoMetadata(file_path)
				splitter.split(metadata)

			print("Processing complete.")

		except MissingInputError as e:
			print(e)
		except subprocess.CalledProcessError as e:
			print(f"FFmpeg/FFprobe error occurred: {e}")
		except Exception as e:
			print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
	Application.run()