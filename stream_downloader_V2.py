import threading
import signal
import traceback
import queue
import subprocess
import os
import configparser
import json
import ctypes
import webbrowser
import time
import sys
from ctypes import wintypes
from pathlib import Path
from datetime import datetime
import tkinter as tk

if getattr(sys, 'frozen', False):
	RUNTIME_DIR = Path(sys._MEIPASS)
	APP_DIR = Path(sys.executable).parent
else:
	RUNTIME_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
	APP_DIR = RUNTIME_DIR

if os.name == 'nt':
	os.add_dll_directory(str(RUNTIME_DIR))
	os.environ["PATH"] = str(RUNTIME_DIR) + os.pathsep + os.environ.get("PATH", "")

import mpv
import pyperclip
import validators
import keyboard


def log(message):
	timestamp = datetime.now().strftime("%H:%M:%S")
	print(f"[{timestamp}] {message}")


def get_secondary_monitor_pos():
	monitors = []
	try:
		user32 = ctypes.windll.user32
		MonitorEnumProc = ctypes.WINFUNCTYPE(
			ctypes.c_int, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

		def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
			r = lprcMonitor.contents
			monitors.append((r.left, r.top))
			return 1

		user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(callback), 0)

		for x, y in monitors:
			if x != 0 or y != 0:
				return x, y
	except Exception:
		pass
	return 0, 0


def hide_taskbar_icon(window_title, is_boss_key_active):
	user32 = ctypes.windll.user32
	hwnd = 0

	for _ in range(10):
		time.sleep(0.5)
		hwnd = user32.FindWindowW(None, window_title) or user32.FindWindowW(None, f"{window_title} - mpv")
		if hwnd:
			break

	if hwnd:
		GWL_EXSTYLE = -20
		WS_EX_APPWINDOW = 0x00040000
		WS_EX_TOOLWINDOW = 0x00000080
		SWP_NOMOVE = 0x0002
		SWP_NOSIZE = 0x0001
		SWP_NOZORDER = 0x0004
		SWP_FRAMECHANGED = 0x0020

		if ctypes.sizeof(ctypes.c_void_p) == 8:
			GetWindowLong = user32.GetWindowLongPtrW
			SetWindowLong = user32.SetWindowLongPtrW
		else:
			GetWindowLong = user32.GetWindowLongW
			SetWindowLong = user32.SetWindowLongW

		style = GetWindowLong(hwnd, GWL_EXSTYLE)
		style = (style & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
		SetWindowLong(hwnd, GWL_EXSTYLE, style)
		user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)

		if is_boss_key_active:
			user32.ShowWindow(hwnd, 0)

	return hwnd


class AppConfig:
	def __init__(self):
		self.ini_path = APP_DIR / 'stream_downloader_V2.ini'
		self.config = configparser.ConfigParser(interpolation=None)
		self.default_path = Path('.')
		self.metadata_map = {}
		self.mpv_kwargs = {}
		self.auto_domains = []
		self.yt_dlp_path = 'yt-dlp'
		self._load_configuration()

	def _load_configuration(self):
		if not self.ini_path.exists():
			log(f"WARNING: Configuration file not found at {self.ini_path}")

		self.config.read(self.ini_path)
		self.default_path = Path(self.config.get('Default', 'path', fallback='.'))

		if 'Metadata' in self.config:
			for domain, keys_str in self.config.items('Metadata'):
				self.metadata_map[domain] = [k.strip() for k in keys_str.split(',')]

		if 'MPV' in self.config:
			for key, value in self.config.items('MPV'):
				val_lower = value.lower()
				if val_lower in ('true', 'yes'):
					self.mpv_kwargs[key] = True
				elif val_lower in ('false', 'no'):
					self.mpv_kwargs[key] = False
				elif value.lstrip('-').isdigit():
					self.mpv_kwargs[key] = int(value)
				else:
					self.mpv_kwargs[key] = value

		if 'AutoDomains' in self.config:
			for key, value in self.config.items('AutoDomains'):
				self.auto_domains.append(value.lower())

		if not self.auto_domains:
			log("WARNING: AutoDomains list is empty. Clipboard monitoring will not trigger.")
		else:
			log(f"Config loaded. AutoDomains listening for: {', '.join(self.auto_domains)}")

		yt_path = APP_DIR / 'yt-dlp.exe'
		self.yt_dlp_path = str(yt_path) if yt_path.exists() else 'yt-dlp'

	def get_output_dir(self, url):
		output_dir = self.default_path
		if 'Keywords' in self.config:
			for keyword, path_str in self.config.items('Keywords'):
				if keyword in url.lower():
					output_dir = Path(path_str)
					break
		output_dir.mkdir(parents=True, exist_ok=True)
		return output_dir


class ConsoleManager:
	def __init__(self):
		kernel32 = ctypes.WinDLL('kernel32')
		self.user32 = ctypes.WinDLL('user32')
		self.hwnd = kernel32.GetConsoleWindow()

	def hide(self):
		if self.hwnd:
			self.user32.ShowWindow(self.hwnd, 0)
			log("Console window hidden on startup. Press CTRL+C on the stream list to toggle visibility.")

	def toggle(self):
		if self.hwnd:
			if self.user32.IsWindowVisible(self.hwnd):
				self.user32.ShowWindow(self.hwnd, 0)
				log("Console window manually hidden.")
			else:
				self.user32.ShowWindow(self.hwnd, 5)
				log("Console window manually revealed.")


class OverlayUI:
	def __init__(self, toggle_console_callback, quit_callback):
		self.toggle_console_callback = toggle_console_callback
		self.quit_callback = quit_callback
		self.root = tk.Tk()
		self._drag_data = {"x": 0, "y": 0}
		self.text_widget = None
		self.border_frame = None
		self.compact_canvas = None
		self.is_compact = False
		self._setup_window()

	def _setup_window(self):
		target_x, target_y = get_secondary_monitor_pos()
		self.root.overrideredirect(True)
		self.root.attributes("-alpha", 0.8)
		self.root.attributes("-topmost", True)
		self.root.geometry(f"+{target_x + 10}+{target_y + 10}")

		self.border_frame = tk.Frame(self.root, bg="#050505", padx=1, pady=1)
		self.border_frame.pack(fill=tk.BOTH, expand=True)

		self.text_widget = tk.Text(
			self.border_frame,
			bg="#1a1a1a",
			fg="#d8b4e2",
			font=("Consolas", 10),
			borderwidth=0,
			highlightthickness=0,
			padx=10,
			pady=10,
			width=100,
			height=2
		)
		self.text_widget.pack(fill=tk.BOTH, expand=True)

		self.compact_canvas = tk.Canvas(
			self.root,
			width=30,
			height=30,
			bg="#1a1a1a",
			highlightthickness=1,
			highlightbackground="#050505"
		)
		self.compact_canvas.create_oval(10, 10, 22, 22, fill="#d8b4e2", outline="")

		self._bind_events()
		log(f"Overlay GUI initialized at position ({target_x + 10}, {target_y + 10}).")

	def _bind_events(self):
		def start_drag_text(event):
			self.text_widget.focus_set()
			self._drag_data["x"] = event.x
			self._drag_data["y"] = event.y

		def start_drag_canvas(event):
			self.compact_canvas.focus_set()
			self._drag_data["x"] = event.x
			self._drag_data["y"] = event.y

		def do_drag(event):
			x = self.root.winfo_x() - self._drag_data["x"] + event.x
			y = self.root.winfo_y() - self._drag_data["y"] + event.y
			self.root.geometry(f"+{x}+{y}")

		def local_toggle_console(event):
			self.toggle_console_callback()
			return "break"

		def local_quit_program(event):
			log("Ctrl+X pressed on GUI. Exiting program...")
			self.quit_callback()
			return "break"

		def local_toggle_compact(event):
			self.is_compact = not self.is_compact
			if self.is_compact:
				self.border_frame.pack_forget()
				self.compact_canvas.pack()
				self.compact_canvas.focus_set()
			else:
				self.compact_canvas.pack_forget()
				self.border_frame.pack(fill=tk.BOTH, expand=True)
				self.text_widget.focus_set()
			return "break"

		self.text_widget.bind("<ButtonPress-1>", start_drag_text)
		self.text_widget.bind("<B1-Motion>", do_drag)
		self.compact_canvas.bind("<ButtonPress-1>", start_drag_canvas)
		self.compact_canvas.bind("<B1-Motion>", do_drag)

		self.text_widget.bind("<Control-c>", local_toggle_console)
		self.text_widget.bind("<Control-x>", local_quit_program)
		self.text_widget.bind("<Control-h>", local_toggle_compact)

		self.compact_canvas.bind("<Control-c>", local_toggle_console)
		self.compact_canvas.bind("<Control-x>", local_quit_program)
		self.compact_canvas.bind("<Control-h>", local_toggle_compact)

		self.root.bind("<Control-c>", local_toggle_console)
		self.root.bind("<Control-x>", local_quit_program)
		self.root.bind("<Control-h>", local_toggle_compact)

	def update_streams_display(self, streams):
		self.text_widget.delete(1.0, tk.END)
		if not streams:
			self.text_widget.configure(height=2)
			self.text_widget.insert(tk.END, "Waiting for streams...\n")
		else:
			self.text_widget.configure(height=len(streams) + 1)
			for i, worker in enumerate(streams, 1):
				self.text_widget.insert(tk.END, f"{i}. {worker.status_line}\n")

	def set_boss_key_state(self, is_active):
		if is_active:
			self.root.withdraw()
		else:
			self.root.deiconify()


class StreamWorker(threading.Thread):
	def __init__(self, url, stream_id, output_dir, metadata_map, mpv_kwargs, yt_dlp_path, manager):
		super().__init__()
		self.url = url
		self.stream_id = stream_id
		self.output_dir = output_dir
		self.metadata_map = metadata_map
		self.mpv_kwargs = mpv_kwargs
		self.yt_dlp_path = yt_dlp_path
		self.manager = manager
		self.data_queue = queue.Queue(maxsize=2000)
		self.active = True
		self.recording = False
		self.abandon = False
		self.is_live = True
		self.bytes_written = 0
		self.hwnd = None

		self.streamer_name = f"Stream_{self.stream_id}"
		self.file_path = None
		self.resolution = "?x?"
		self.fps = "?"
		self.player = None

		log(f"[Stream {self.stream_id}] Worker spawned for URL: {self.url}")

	@property
	def status_line(self):
		if self.recording and self.bytes_written > 0:
			size_mb = self.bytes_written / (1024 * 1024)
			size_str = f"{size_mb:.1f}MB"
		else:
			size_str = "PAUSED" if not self.recording else "WAITING"

		path_name = self.file_path.name if self.file_path else "Fetching..."
		return f"[{size_str}] - \"{path_name}\" - {self.resolution} - {self.fps}fps"

	def _fetch_metadata(self):
		log(f"[Stream {self.stream_id}] Fetching yt-dlp metadata...")
		cmd = [self.yt_dlp_path, '--dump-json', '--no-playlist', self.url]
		try:
			result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
			meta = json.loads(result)
		except FileNotFoundError:
			log(f"[Stream {self.stream_id}] CRITICAL: yt-dlp executable not found!")
			meta = {}
		except (subprocess.CalledProcessError, json.JSONDecodeError):
			log(f"[Stream {self.stream_id}] Failed to fetch metadata. Using defaults.")
			meta = {}

		keys_to_check = self.metadata_map.get('default', ['id'])
		for domain, keys in self.metadata_map.items():
			if domain in self.url.lower():
				keys_to_check = keys
				break

		for key in keys_to_check:
			if meta.get(key):
				self.streamer_name = str(meta.get(key)).replace(' ', '_')
				break

		width = meta.get('width')
		height = meta.get('height')
		if width and height:
			self.resolution = f"{width}x{height}"
		self.fps = meta.get('fps', '?')

		live_status = meta.get('live_status')
		is_live_flag = meta.get('is_live')

		if live_status in ['not_live', 'was_live']:
			self.is_live = False
		elif is_live_flag is False:
			self.is_live = False
		else:
			self.is_live = True

		log(f"[Stream {self.stream_id}] Metadata acquired: {self.streamer_name} ({self.resolution} @ {self.fps}fps) - Live Status: {self.is_live}")

	def _setup_player(self):
		kwargs = self.mpv_kwargs.copy()
		kwargs['title'] = self.streamer_name
		self.player = mpv.MPV(**kwargs)

		@self.player.event_callback('shutdown')
		def on_shutdown(event):
			if self.active:
				log(f"[Stream {self.stream_id}] MPV window closed manually. Terminating stream.")
				self.active = False

		def update_overlay():
			lines = []
			if self.recording:
				lines.append(f'Rec...')
			self.player.osd_msg1 = "\n".join(lines)

		@self.player.python_stream(f'pystream{self.stream_id}')
		def read_stream():
			while self.active:
				try:
					chunk = self.data_queue.get(timeout=0.2)
					if chunk:
						yield chunk
				except queue.Empty:
					continue
				except Exception:
					break

		@self.player.on_key_press('q')
		def toggle_recording():
			self.recording = not self.recording
			log(f"[Stream {self.stream_id}] Recording status toggled to: {'ACTIVE' if self.recording else 'PAUSED'}")
			update_overlay()

		@self.player.on_key_press('x')
		def close_stream():
			log(f"[Stream {self.stream_id}] Stream closed via 'x' hotkey.")
			self.active = False
			self.player.quit()

		# Prevent ctrl+c in cmd window from closing the mpv streams
		@self.player.on_key_press('ctrl+c')
		def toggle_console_from_mpv():
			log(f"[Toggled console from an MPV window]")
			self.manager.console.toggle()

		@self.player.on_key_press('ctrl+x')
		def abandon_stream():
			log(f"[Stream {self.stream_id}] Stream abandoned via 'ctrl+x' hotkey. Marking for deletion.")
			self.abandon = True
			self.active = False
			self.player.quit()

		@self.player.on_key_press('ctrl+b')
		def open_in_browser():
			log(f"[Stream {self.stream_id}] Opening URL in browser.")
			webbrowser.open(self.url)

		@self.player.on_key_press('alt+1')
		def resize_1():
			geo = str(self.mpv_kwargs.get('geometry', '40%'))
			self.player.geometry = geo
			log(f"[Stream {self.stream_id}] Resized to default ({geo})")

		@self.player.on_key_press('alt+2')
		def resize_2():
			w = self.player.osd_width
			h = self.player.osd_height
			if w and h:
				self.player.geometry = f"{int(w * 0.5)}x{int(h * 0.5)}"
				log(f"[Stream {self.stream_id}] Resized to 50% of current size")

		@self.player.on_key_press('alt+3')
		def resize_3():
			w = self.player.osd_width
			h = self.player.osd_height
			if w and h:
				self.player.geometry = f"{int(w / 3)}x{int(h / 3)}"
				log(f"[Stream {self.stream_id}] Resized to 33% of current size")

		@self.player.on_key_press('alt+4')
		def resize_4():
			w = self.player.osd_width
			h = self.player.osd_height
			if w and h:
				self.player.geometry = f"{int(w * 0.25)}x{int(h * 0.25)}"
				log(f"[Stream {self.stream_id}] Resized to 25% of current size")

	def _execute_taskbar_hiding(self):
		self.hwnd = hide_taskbar_icon(self.streamer_name, self.manager.boss_key_active)

	def _process_download_stream(self):
		dl_cmd = [self.yt_dlp_path, '-o', '-', self.url]
		try:
			downloader = subprocess.Popen(dl_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
		except FileNotFoundError:
			log(f"[Stream {self.stream_id}] CRITICAL: yt-dlp executable not found at {self.yt_dlp_path}")
			self.active = False
			if self.player:
				self.player.quit()
			return

		file_handle = None

		try:
			log(f"[Stream {self.stream_id}] Active and waiting for data chunks...")
			while self.active:
				chunk = downloader.stdout.read(65536)
				if not chunk:
					log(f"[Stream {self.stream_id}] Source data stream ended.")
					break

				if self.recording:
					if file_handle is None:
						file_handle = open(self.file_path, 'ab')
						log(f"[Stream {self.stream_id}] Writing data to disk initiated.")
					file_handle.write(chunk)
					self.bytes_written += len(chunk)

				try:
					self.data_queue.put(chunk, timeout=1)
				except queue.Full:
					pass
		finally:
			self.active = False
			if file_handle is not None:
				file_handle.close()
				size_mb = self.bytes_written / (1024 * 1024)
				log(f"[Stream {self.stream_id}] File handle closed. Final size: {size_mb:.2f} MB")

			downloader.terminate()
			if self.player:
				try:
					self.player.terminate()
				except Exception:
					pass

			if self.abandon and self.file_path and self.file_path.exists():
				try:
					self.file_path.unlink()
					log(f"[Stream {self.stream_id}] Successfully deleted abandoned file: {self.file_path.name}")
				except OSError:
					log(f"[Stream {self.stream_id}] Error deleting abandoned file: {self.file_path.name}")

			log(f"[Stream {self.stream_id}] Thread gracefully terminated.")

	def run(self):
		self._fetch_metadata()

		if not self.is_live:
			log(f"[Stream {self.stream_id}] Aborting: URL is a standard VOD, not an active live stream.")
			self.active = False
			return

		self._setup_player()

		timestamp = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
		self.file_path = self.output_dir / f'{self.streamer_name}_{timestamp}.mp4'
		log(f"[Stream {self.stream_id}] Target save path: {self.file_path}")

		self.player.play(f'python://pystream{self.stream_id}')

		threading.Thread(target=self._execute_taskbar_hiding, daemon=True).start()

		self._process_download_stream()


class StreamManager:
	def __init__(self):
		log("Initializing StreamManager...")
		self.streams = []
		self.counter = 0
		self.url_queue = queue.Queue()
		self.last_clipboard = ""
		self.boss_key_active = False
		self.boss_key_toggle_requested = False

		self.config = AppConfig()
		self.console = ConsoleManager()
		self.ui = OverlayUI(self.console.toggle, self.quit_program)

		self.console.hide()

	def quit_program(self):
		self.ui.root.quit()

	def request_boss_key_toggle(self):
		self.boss_key_toggle_requested = True

	def _process_boss_key(self):
		if self.boss_key_toggle_requested:
			self.boss_key_toggle_requested = False
			self.boss_key_active = not self.boss_key_active

			self.ui.set_boss_key_state(self.boss_key_active)

			if self.boss_key_active:
				for s in self.streams:
					if s.hwnd:
						ctypes.windll.user32.ShowWindow(s.hwnd, 0)
				log("Boss Key ACTIVATED: All windows hidden.")
			else:
				for s in self.streams:
					if s.hwnd:
						ctypes.windll.user32.ShowWindow(s.hwnd, 5)
				log("Boss Key DEACTIVATED: Windows restored.")

	def _monitor_clipboard(self):
		try:
			current_clipboard = pyperclip.paste()
			if current_clipboard:
				current_clipboard = current_clipboard.strip()
				if current_clipboard != self.last_clipboard:
					self.last_clipboard = current_clipboard
					if validators.url(current_clipboard):
						url_lower = current_clipboard.lower()
						if any(domain in url_lower for domain in self.config.auto_domains):
							compare_url = current_clipboard.rstrip('/')
							is_active = any(s.url.rstrip('/') == compare_url for s in self.streams if s.is_alive())
							in_queue = compare_url in [u.rstrip('/') for u in list(self.url_queue.queue)]

							if not is_active and not in_queue:
								log(f"[Manager] AutoDomain matched from clipboard: {url_lower}")
								self.url_queue.put(current_clipboard)
							else:
								log(f"[Manager] Ignored duplicate URL: {current_clipboard}")
		except Exception as e:
			log(f"[Manager] Clipboard access warning: {e}")

	def _spawn_workers(self):
		while not self.url_queue.empty():
			url = self.url_queue.get()
			self.counter += 1
			output_dir = self.config.get_output_dir(url)
			worker = StreamWorker(
				url,
				self.counter,
				output_dir,
				self.config.metadata_map,
				self.config.mpv_kwargs,
				self.config.yt_dlp_path,
				self
			)
			self.streams.append(worker)
			worker.start()

	def update_loop(self):
		self._process_boss_key()
		self._monitor_clipboard()
		self._spawn_workers()

		self.streams = [s for s in self.streams if s.is_alive()]
		self.ui.update_streams_display(self.streams)

		self.ui.root.after(100, self.update_loop)

	def run(self):
		keyboard.add_hotkey('ctrl+`', self.request_boss_key_toggle)

		log("Starting main update loop...")
		self.update_loop()

		try:
			self.ui.root.mainloop()
		except KeyboardInterrupt:
			log("Keyboard interrupt received. Initiating cleanup...")
		finally:
			self.cleanup()

	def cleanup(self):
		log("Initiating cleanup sequence...")
		for s in self.streams:
			s.active = False
		for s in self.streams:
			if s.is_alive():
				s.join()
		log("Cleanup complete. Shutting down.")


if __name__ == '__main__':
	# Stop program from terminating on ctrl+c in the cmd window
	signal.signal(signal.SIGINT, signal.SIG_IGN)

	try:
		manager = StreamManager()
		manager.run()
	except Exception as e:
		log(f"FATAL ERROR: {str(e)}")
		traceback.print_exc()
		input("\nPress Enter to exit...")