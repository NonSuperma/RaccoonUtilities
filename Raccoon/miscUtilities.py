from pathlib import Path
from typing import Dict, Any
import subprocess
import json
import sys


def seconds_to_hhmmss(s: float) -> str:
    sign = "-" if s < 0 else ""
    s = abs(s)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f'{sign}{h:02d}:{m:02d}:{sec:06.3f}'


def hhmmss_to_seconds(timestamp: str) -> float:
    sign = -1 if '-' in timestamp else 1
    parts = timestamp.split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid format: expected 'HH:MM:SS.sss', got '{timestamp}'")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return hours * 3600 + minutes * 60 + seconds * sign


def add_times(time_list: list[str] | list[float]) -> str:
    total = 0
    _format = 's' if time_list is list[str] else 'hh'
    for t in time_list:
        if _format == 's':
            total += t
        else:
            total += hhmmss_to_seconds(t)
    if _format == 's':
        return total
    else:
        return seconds_to_hhmmss(total)


def console_clear_n(n: int) -> None:
    sys.stdout.flush()
    for i in range(n):
        sys.stdout.write('\x1b[1A\x1b[2K')
    sys.stdout.flush()


def get_bundled_file_path(file_name: str) -> str:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        file_path = base_path / file_name
        if file_path.is_file():
            return str(file_path)
    return file_name


def get_media_file_data(file_path: Path) -> Dict[Any, Any] | None:
    extensions = ['png', 'jpg', 'jpeg', 'webp', 'ico', 'gif', 'bmp', 'tiff', 'svg', 'heic', 'avif']
    if file_path.suffix in extensions:
        return None

    ffprobe_path = get_bundled_file_path('ffprobe.exe')

    cmd_format = [
        ffprobe_path,
        '-select_streams', 'a',
        '-show_entries', 'format=format_name,duration,size,bit_rate:format_tags',
        '-print_format', 'json',
        str(file_path)
    ]
    ffprobeOutput_format = subprocess.run(cmd_format, capture_output=True, check=True)
    ffprobeOutputJson_format = json.loads(ffprobeOutput_format.stdout)

    cmd_audio = [
        ffprobe_path,
        '-select_streams', 'a',
        '-show_entries',
        'format=format_name,duration,size,bit_rate:stream=index,codec_name,sample_rate,bits_per_raw_sample,channels,bit_rate:format_tags:stream_tags',
        '-print_format', 'json',
        str(file_path)
    ]
    ffprobeOutput_audio = subprocess.run(cmd_audio, capture_output=True, check=True)
    ffprobeOutputJson_audio = json.loads(ffprobeOutput_audio.stdout)

    cmd_video = [
        ffprobe_path,
        '-select_streams', 'v',
        '-show_entries', 'stream=index,codec_name,width,height,pix_fmt:format_tags:stream_tags',
        '-print_format', 'json',
        str(file_path)
    ]
    ffprobeOutput_video = subprocess.run(cmd_video, capture_output=True, check=True)
    ffprobeOutputJson_video = json.loads(ffprobeOutput_video.stdout)

    results = {}
    results.update(ffprobeOutputJson_format)
    results.update({'video': ffprobeOutputJson_video['streams']})
    results.update({'audio': ffprobeOutputJson_audio['streams']})

    def convert_numeric_keys_values(d):
        new_dict = {}
        for key, value in d.items():
            if isinstance(key, str):
                try:
                    if key.isdigit():
                        key = int(key)
                    else:
                        key = float(key)
                except ValueError:
                    pass

            if isinstance(value, dict):
                value = convert_numeric_keys_values(value)

            elif isinstance(value, list):
                converted_list = []
                for item in value:
                    converted_list.append(convert_numeric_keys_values(item))
                value = converted_list

            elif isinstance(value, str):
                try:
                    if value.isdigit():
                        value = int(value)
                    else:
                        value = float(value)
                except ValueError:
                    pass

            new_dict[key] = value
        return new_dict

    results = convert_numeric_keys_values(results)

    return results


def subprocess_run_with_spinner(cmd, progress_message='Running...', **kwargs):
	"""
	Executes a subprocess command while displaying a terminal spinner.

	Args:
		cmd (list): The command and arguments to execute.
		progress_message (str): The text to display next to the spinner.

	Raises:
		subprocess.CalledProcessError: If the subprocess exits with a non-zero code.
	"""
	console = Console()

	kwargs.setdefault('spinner', 'dots12')
	kwargs.setdefault('spinner_style', 'yellow')
	with console.status(f'{progress_message}', **kwargs):
		process = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True
		)

		stdout_text, _ = process.communicate()
		exit_code = process.returncode

	if exit_code != 0:
		raise subprocess.CalledProcessError(
			returncode=exit_code,
			cmd=cmd,
			output=stdout_text
		)
