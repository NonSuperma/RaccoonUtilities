import subprocess
import json
from pathlib import Path
from typing import Any, Dict
from Raccoon.miscUtilities import seconds_to_hhmmss


def get_audio_data(pathToFile: Path) -> None or Dict[Any, Any]:
    extensions = ['png', 'jpg', 'jpeg', 'webp', 'ico', 'gif', 'bmp', 'tiff', 'svg', 'heic', 'avif']
    if pathToFile.suffix in extensions:
        return None

    ffprobeOutput = subprocess.run(
        f'ffprobe '
        f'-select_streams a:0 '
        f'-show_entries format=format_name,duration,size,bit_rate:stream=codec_name,sample_rate,bits_per_raw_sample,channels,bit_rate:format_tags:stream_tags -print_format json "{pathToFile}"',
        shell=True, capture_output=True)
    ffprobeOutputJson = json.loads(ffprobeOutput.stdout)

    results = {}
    results.update({'format': ffprobeOutputJson['format']})
    results.update({'streams': ffprobeOutputJson["streams"][0]})
    tags = {}
    if 'tags' in ffprobeOutputJson['format']:
        tags.update(ffprobeOutputJson['format']['tags'])
        results['format'].pop('tags')

    if 'tags' in ffprobeOutputJson["streams"][0]:
        tags.update(ffprobeOutputJson["streams"][0]['tags'])
        results['streams'].pop('tags')

    results.update({'tags': tags})

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


def get_audio_duration(file_path: Path) -> str or None:
    ffprobeOutput = subprocess.run(
        f'ffprobe '
        f'-show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 '
        f'"{file_path}"',
        shell=True, capture_output=True)

    if ffprobeOutput.returncode != 0:
        print(ffprobeOutput.stdout.decode())
        return None

    else:
        return seconds_to_hhmmss(float(ffprobeOutput.stdout.decode()))
