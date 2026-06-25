import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from Raccoon.windowsUtilities import win_files_path
from Raccoon.miscUtilities import get_media_file_data

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_track(file_path: Path, extension_map: Dict[str, str]) -> None:
	try:
		file_data: Dict[str, Any] = get_media_file_data(file_path)

		if not file_data.get('audio') or not isinstance(file_data['audio'], list):
			logging.warning(f"No valid audio stream found in {file_path}.")
			return

		codec: str = str(file_data['audio'][0].get('codec_name', '')).strip().lower()

		if not codec or not codec.replace('_', '').replace('-', '').isalnum():
			logging.warning(f"Invalid codec format '{codec}' in {file_path}.")
			return

		final_ext: str = f".{extension_map.get(codec, codec)}"
		final_file_path: Path = file_path.with_suffix(final_ext)

		if file_path.suffix.lower() == final_ext:
			logging.info(f"File {file_path.name} already has correct extension.")
			return

		final_file_path.parent.mkdir(parents=True, exist_ok=True)

		command: List[str] = [
			'ffmpeg',
			'-y',
			'-i', str(file_path.resolve()),
			'-c:a', 'copy',
			str(final_file_path.resolve())
		]

		subprocess.run(command, capture_output=True, text=True, check=True)
		logging.info(f"Saved to {final_file_path}")

	except subprocess.CalledProcessError as e:
		logging.error(f"FFmpeg failed for {file_path}. Error: {e.stderr.strip()}")
	except Exception as e:
		logging.error(f"Unexpected error processing {file_path}: {e}")


def main() -> None:
	if not shutil.which('ffmpeg'):
		logging.critical("FFmpeg executable not found in system PATH.")
		return

	extension_map: Dict[str, str] = {
		"aac": "aac",
		"vorbis": "ogg",
		"opus": "opus",
		"flac": "flac",
		"mp3": "mp3",
		"pcm_s16le": "wav"
	}

	try:
		file_paths = win_files_path('tracks')
	except Exception as e:
		logging.critical(f"Failed to retrieve paths: {e}")
		return

	for file_path in file_paths:
		process_track(Path(file_path), extension_map)


if __name__ == '__main__':
	main()