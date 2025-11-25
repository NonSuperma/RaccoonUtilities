import subprocess
import sys
import msvcrt
import os
from datetime import datetime
from pathlib import Path
import colorama
from colorama import Fore
import json
import validators
import time


def get_mpv_path():
	if getattr(sys, 'frozen', False):
		return Path(sys._MEIPASS) / 'mpv.exe'
	return Path('mpv.exe')


def get_ytdlp_path():
	if getattr(sys, 'frozen', False):
		return Path(sys.executable).parent / 'yt-dlp.exe'
	return Path('yt-dlp.exe')


def get_stream_info(yt_dlp_exe, url):
	try:
		cmd = [
			str(yt_dlp_exe),
			'--dump-json',
			'--no-playlist',
			url
		]

		result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
		data = json.loads(result)
		return data
	except subprocess.CalledProcessError:
		return None
	except json.JSONDecodeError:
		return None


def main():
	# Set Window Size (Width=100 chars, Height=30 lines)
	os.system("mode con: cols=60 lines=20")
	os.system("title Stream Recorder")

	colorama.init(autoreset=True)
	mpv_exe = get_mpv_path()
	yt_dlp_exe = get_ytdlp_path()

	print(f'{Fore.CYAN}Checking tools...{Fore.RESET}')
	if not yt_dlp_exe.exists():
		print(f"{Fore.RED}CRITICAL: yt-dlp.exe not found!{Fore.RESET}")
		input("Press Enter to exit...")
		return
	print(f'{Fore.GREEN}All tools there ^^{Fore.RESET}\n')

	urlInput_count = 0
	while True:
		if urlInput_count == 0:
			print('Url: ', end='')
			temp_url = input()
			if validators.url(temp_url):
				url = temp_url
				sys.stdout.write("\033[F\033[K")
				print(f'{Fore.GREEN}'
					  f'Url:{Fore.RESET} {url}')
				break
			urlInput_count += 1

	print(f"{Fore.CYAN}Fetching stream metadata...{Fore.RESET}")
	meta = get_stream_info(yt_dlp_exe, url)
	sys.stdout.write('\x1b[1A\x1b[2K')

	if not meta:
		print(f"{Fore.RED}Error: Could not fetch info.{Fore.RESET}")
	else:

		streamer_name = meta.get('id') or meta.get('display_id')
		stream_title = meta.get('title')
		resolution = f"{meta.get('width')}x{meta.get('height')}"
		vcodec = meta.get('vcodec')
		acodec = meta.get('acodec')

		print(f"\n{Fore.MAGENTA}--- STREAM INFO ---{Fore.RESET}")
		print(f"Streamer:   {Fore.WHITE}{streamer_name}{Fore.RESET}")
		print(f"Title:      {Fore.WHITE}{stream_title}{Fore.RESET}")
		print(f"Quality:    {Fore.WHITE}{resolution}({vcodec} - {acodec}){Fore.RESET}")
		print(f"-------------------")

		# with open('data.json', 'w') as f:
		# 	f.write(json.dumps(meta, indent=4))

	time_now = datetime.now()
	timestamp = time_now.strftime("%Y-%m-%d_%H-%M-%S")

	if streamer_name:
		filename = f'{streamer_name}_{timestamp}.mkv'
	else:
		filename = f'stream_capture_{timestamp}.mkv'

	output_dir = Path(r'E:\Other\OBS_Output')
	file_path = output_dir / filename

	print(f"{Fore.MAGENTA}Saving to:\n"
		  f"{file_path}{Fore.RESET}")
	print(f"{Fore.CYAN}Press 'q' to stop recording.{Fore.RESET}")

	window_title = stream_title if stream_title else 'Stream'

	dl_cmd = [
		str(yt_dlp_exe),
		'--ignore-errors',
		'--no-live-from-start',
		'--retries', 'infinite',
		'--fragment-retries', 'infinite',
		'--skip-unavailable-fragments',
		'--wait-for-video', '15',
		'--no-part',
		'-o', '-',
		url
	]

	downloader = subprocess.Popen(
		dl_cmd,
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL
	)

	mpv_cmd = [
		str(mpv_exe),
		# --- TITLE FIXES ---
		f'--title={window_title} [REC]',  # Force Windows Taskbar Name
		f'--force-media-title={window_title}',  # Force Internal Metadata Name
		f'--script-opts=osc-title={window_title} [REC]',  # Force the UI Overlay Text
		# -------------------
		'--cache=yes',
		'--demuxer-max-bytes=100M',

		# --- PICTURE IN PICTURE SETTINGS ---
		'--no-border',
		'--geometry=35%-15-50',  # 25% width, Bottom-Right corner (adjusted for Taskbar)
		'--force-window=immediate',
		# -----------------------------------

		'-'
	]

	player = subprocess.Popen(
		mpv_cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL
	)

	mpv_active = True
	total_bytes = 0
	start_time = time.time()

	try:
		with open(file_path, 'wb') as f:
			while True:
				chunk = downloader.stdout.read(65536)

				if not chunk:
					if downloader.poll() is not None:
						break
					continue

				f.write(chunk)
				total_bytes += len(chunk)

				if mpv_active:
					try:
						player.stdin.write(chunk)
						player.stdin.flush()
					except (OSError, BrokenPipeError, ValueError):
						print(f"\n{Fore.CYAN}MPV closed. Recording continues...{Fore.RESET}")
						mpv_active = False

				if msvcrt.kbhit():
					key = msvcrt.getch()
					if key.lower() == b'q':
						print(f"\n{Fore.RED}Stopping recording...{Fore.RESET}")
						break

				if total_bytes % (1024 * 1024) == 0:
					elapsed_seconds = int(time.time() - start_time)
					hours, rem = divmod(elapsed_seconds, 3600)
					minutes, seconds = divmod(rem, 60)
					time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
					if total_bytes / (1024 * 1024) > 1000:
						sys.stdout.write(f"\rCaptured: {total_bytes / (1024 * 1024 * 1024):.1f} GB | Time: {time_str}")
					else:
						sys.stdout.write(f"\rCaptured: {total_bytes / (1024 * 1024):.1f} MB | Time: {time_str}")
					sys.stdout.flush()

	except Exception as e:
		print(f"\nError: {e}")

	if mpv_active:
		player.terminate()
	downloader.terminate()
	input(f"\n{Fore.GREEN}Done. Saved to {filename}\n"
		  f"Press Enter to exit{Fore.RESET}")


if __name__ == '__main__':
	main()
