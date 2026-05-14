from pathlib import Path
import os
import subprocess
from playsound3 import playsound
from Raccoon.windowsUtilities import win_file_path, count_open_windows
from Raccoon.miscUtilities import seconds_to_hhmmss, get_bundled_file_path

if os.name == 'nt':
	current_dir = os.path.dirname(os.path.abspath(__file__))
	os.add_dll_directory(current_dir)
	os.environ["PATH"] = current_dir + os.pathsep + os.environ.get("PATH", "")


FFMPEG_PATH = get_bundled_file_path('ffmpeg.exe')


def preview_and_cut(input_path, output_path):
	import mpv
	input_path = str(input_path)
	output_path = str(output_path)

	player = mpv.MPV(
		input_default_bindings=True,
		input_vo_keyboard=True,
		osc=True,
		border=False,
		osd_font_size=28,
		keep_open=True
	)

	start_time = 0.0
	end_time: float | None = None
	start_marked = False
	video_duration = None
	cut_authorized = False

	def update_overlay():
		lines = ["Keybinds: S (Start) | E (End) | Q (Quit & Cut)"]
		if start_marked:
			lines.append(f'Start marked at: {seconds_to_hhmmss(start_time)}')
		if end_time is not None:
			lines.append(f'End marked at: {seconds_to_hhmmss(end_time)}')
		player.osd_msg1 = "\n".join(lines)

	@player.property_observer('duration')
	def on_duration(name, value):
		print(f'{name}: {value}')
		nonlocal video_duration
		if value is not None:
			video_duration = value

	@player.on_key_press('s')
	def set_start():
		nonlocal start_time, start_marked
		start_time = player.time_pos or 0.0
		start_marked = True
		update_overlay()
		print(f'Start marked at: {seconds_to_hhmmss(start_time)}')

	@player.on_key_press('e')
	def set_end():
		nonlocal end_time
		end_time = player.time_pos or 0.0
		update_overlay()
		print(f'End marked at: {seconds_to_hhmmss(end_time)}')

	@player.on_key_press('q')
	def close_player():
		nonlocal cut_authorized
		if end_time is not None and start_time >= end_time:
			player.show_text('Warning: Start time must be before End time!', duration=3000)
		else:
			cut_authorized = True
			player.quit()

	update_overlay()

	player.play(input_path)
	player.wait_for_playback()
	player.terminate()

	if not cut_authorized:
		print("Cutting aborted: Player closed without pressing Q.")
		return False

	if end_time is None:
		if video_duration is None:
			return False
		end_time = video_duration

	duration = end_time - start_time

	print(f"Extracting clip from {start_time:.3f}s to {end_time:.3f}s...")

	cmd = [
		FFMPEG_PATH, '-y', '-nostdin',
		'-v', 'error',
		'-ss', str(start_time),
		'-i', input_path,
		'-t', str(duration),
		'-c', 'copy',
		'-avoid_negative_ts', 'make_zero',
		output_path
	]
	result = subprocess.run(cmd)

	return result.returncode == 0


def main():
	video_path = win_file_path('video')
	output_path = video_path.parent / (str(video_path.stem) + '_cut.mp4')

	success = preview_and_cut(str(video_path), str(output_path))

	if success:
		audio_path = get_bundled_file_path(r'SourceFiles\au5-1.mp3')
		playsound(audio_path)
		if count_open_windows(output_path.parent.name) == 0:
			os.startfile(output_path.name)


if __name__ == '__main__':
	main()
