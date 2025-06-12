from pathlib import Path
from Raccoon.miscUtilities import seconds_to_hhmmss


def get_bitrate(sound_input_path: Path) -> dict[str, int] or None:

    extensions = ['png', 'jpg', 'jpeg', 'webp']
    if sound_input_path.suffix in extensions:
        return None

    ffprobeOutput = sp.run(
        f'ffprobe '
        f'-v quiet '
        f'-select_streams a:0 '
        f'-show_entries stream=bit_rate '
        f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
        shell=True, capture_output=True).stdout.decode().strip()
    _type = 'bitrate'

    if ffprobeOutput == 'N/A':
        ffprobeOutput = sp.run(
            f'ffprobe '
            f'-v quiet '
            f'-select_streams a:0 '
            f'-show_entries stream=sample_rate '
            f'-of default=noprint_wrappers=1:nokey=1 "{sound_input_path}"',
            shell=True, capture_output=True).stdout.decode().strip()
        _type = 'samplerate'

    output = {
        _type: int(ffprobeOutput)
    }
    return output


def get_audio_encoding(file_path: Path) -> str or None:
    extensions = ['.png', '.jpg', '.jpeg', '.webp']
    if file_path.suffix in extensions:
        return None

    ffprobeOutput = sp.run(
        f'ffprobe '
        f'-select_streams a:0 '
        f'-show_entries stream=codec_name -of default=nokey=1:noprint_wrappers=1 '
        f'"{file_path}"',
        shell=True, capture_output=True)
    return ffprobeOutput.stdout.decode().strip()


def get_audio_duration(file_path: Path) -> str or None:
    ffprobeOutput = sp.run(
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