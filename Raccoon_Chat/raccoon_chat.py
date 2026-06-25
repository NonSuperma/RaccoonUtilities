import os
import json
import time
import ctypes
import re
import locale
import threading
import tkinter as tk
from contextlib import suppress
from tkinter import ttk, font as tkfont
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple

from google import genai
from google.genai import types

with suppress(Exception):
	locale.setlocale(locale.LC_ALL, '')
	locale.setlocale(locale.LC_NUMERIC, 'C')


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

@dataclass
class Theme:
	bg_main: str = "#050505"
	bg_panel: str = "#1a1a1a"
	bg_input: str = "#2a2a2a"
	bg_button: str = "#333333"
	bg_separator: str = "#3a3a3a"
	fg_text: str = "#ffffff"
	fg_accent: str = "#d8b4e2"
	fg_muted: str = "#888888"
	fg_green: str = "#90ee90"
	fg_grey: str = "#aaaaaa"


@dataclass
class AppConfig:
	api_key: str = field(init=False)
	history_file: Path = Path("chat_history.json")
	models: List[str] = field(default_factory=lambda: [
		'gemini-3.5-flash',
		'gemini-3.1-flash-lite',
		'gemini-2.5-flash',
		'gemini-2.0-flash',
		'gemini-2.5-pro'
	])
	current_model: str = 'gemini-3.5-flash'
	temperature: float = 1.4
	top_k: int = 64
	top_p: float = 0.95
	max_tokens: int = 8192
	presence_penalty: float = 0.4
	frequency_penalty: float = 0.4
	thinking_levels: List[str] = field(default_factory=lambda: ["LOW", "MEDIUM", "HIGH"])
	thinking_level: str = "MEDIUM"
	is_paid_tier: bool = True

	def __post_init__(self) -> None:
		key_file = Path("api_key.txt")
		if key_file.exists():
			self.api_key = key_file.read_text(encoding="utf-8").strip()
		else:
			self.api_key = os.environ.get("GEMINI_API_KEY", "")

	def get_model_caps(self, model_name: str) -> Dict[str, Any]:
		return {
			"max_tokens": 4096 if "lite" in model_name else 8192,
			"penalties": not any(v in model_name for v in ["3.5", "3.1", "2.0"]),
			"max_rpm": 15,
			"max_tpm": 1000000,
			"cost_in": 1.25 if "pro" in model_name else 0.075,
			"cost_out": 5.00 if "pro" in model_name else 0.30
		}


class UsageTracker:
	def __init__(self, max_rpm: int = 15, max_tpm: int = 1000000) -> None:
		self.max_rpm = max_rpm
		self.max_tpm = max_tpm
		self.request_timestamps: List[float] = []
		self.token_history: List[Tuple[float, int]] = []
		self.session_input_tokens = 0
		self.session_output_tokens = 0
		self.lock = threading.Lock()

	def clean_old_data(self) -> None:
		cutoff = time.time() - 60.0
		with self.lock:
			self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff]
			self.token_history = [(ts, tc) for ts, tc in self.token_history if ts > cutoff]

	def can_request(self, is_paid: bool) -> bool:
		if is_paid:
			return True
		self.clean_old_data()
		with self.lock:
			return len(self.request_timestamps) < self.max_rpm

	def add_request_timestamp(self) -> None:
		with self.lock:
			self.request_timestamps.append(time.time())

	def add_token_usage(self, input_tok: int, output_tok: int) -> None:
		with self.lock:
			self.session_input_tokens += input_tok
			self.session_output_tokens += output_tok
			self.token_history.append((time.time(), input_tok + output_tok))

	def get_stats(self) -> Tuple[int, int]:
		self.clean_old_data()
		with self.lock:
			return len(self.request_timestamps), sum(tc for ts, tc in self.token_history)


class Formatter:
	@staticmethod
	def format_quotes(text: str) -> str:
		if text.count('"') % 2 != 0 or text.count('"') == 0:
			return text

		parts = text.split('"')
		formatted_text = parts[0]

		for i in range(1, len(parts), 2):
			quote_content = parts[i]
			after_quote = parts[i + 1]

			if not formatted_text.endswith('\n') and formatted_text.strip():
				formatted_text = formatted_text.rstrip() + '\n'

			formatted_text += f'"{quote_content}"'

			same_line_text = after_quote.split('\n')[0].strip()
			if same_line_text.startswith(('-', '–', '—')):
				after_quote = re.sub(r'^[ \t]*[-–—][ \t]*', ' - ', after_quote)
			elif same_line_text and same_line_text[0].isalpha():
				after_quote = re.sub(r'^[ \t]*', ' - ', after_quote)

			formatted_text += after_quote

		return formatted_text


class GeminiManager:
	def __init__(self, config: AppConfig) -> None:
		self.config = config
		self.client = genai.Client(api_key=self.config.api_key)
		self.chat_sessions: Dict[str, Any] = {}
		self.current_session_id: Optional[str] = None
		self.active_chat = None
		self.usage_tracker = UsageTracker()
		self.is_compressing = False
		self.load_history()

	def load_history(self) -> None:
		if self.config.history_file.exists():
			self.chat_sessions = json.loads(self.config.history_file.read_text(encoding='utf-8'))

		if not self.chat_sessions:
			self.create_new_session()
		else:
			self.current_session_id = list(self.chat_sessions.keys())[-1]
			self._init_chat_object()

	def save_history(self) -> None:
		self.config.history_file.write_text(json.dumps(self.chat_sessions, indent=2), encoding='utf-8')

	def create_new_session(self) -> None:
		session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		self.chat_sessions[session_id] = {"type": "normal", "history": []}
		self.current_session_id = session_id
		self._init_chat_object()
		self.save_history()

	def create_rp_session(self, configs: dict) -> None:
		session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		self.chat_sessions[session_id] = {
			"type": "roleplay",
			"config": configs,
			"summary": "",
			"summarized_index": 1,
			"history": [{"role": "ai", "content": configs["first_message"]}]
		}
		self.current_session_id = session_id
		self._init_chat_object()
		self.save_history()

	def delete_session(self, session_id: str) -> None:
		if session_id in self.chat_sessions:
			del self.chat_sessions[session_id]
			self.save_history()

			if self.current_session_id == session_id:
				if self.chat_sessions:
					self.current_session_id = list(self.chat_sessions.keys())[-1]
					self._init_chat_object()
				else:
					self.create_new_session()

	def rename_session(self, old_id: str, new_id: str) -> None:
		if old_id in self.chat_sessions and new_id not in self.chat_sessions:
			self.chat_sessions = {
				(new_id if key == old_id else key): value
				for key, value in self.chat_sessions.items()
			}
			if self.current_session_id == old_id:
				self.current_session_id = new_id
			self.save_history()

	def switch_session(self, session_id: str) -> None:
		if session_id in self.chat_sessions:
			self.current_session_id = session_id
			self._init_chat_object()

	def compress_history(self, session_id: str) -> None:
		if self.is_compressing:
			return

		session = self.chat_sessions[session_id]
		history = session.get("history", [])

		if session.get("type") != "roleplay":
			return

		start_idx = session.get("summarized_index", 1)
		end_idx = len(history) - 6

		if end_idx - start_idx < 6:
			return

		def task() -> None:
			self.is_compressing = True
			try:
				messages = history[start_idx:end_idx]
				text_to_compress = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
				prompt = (f"Zaktualizuj podsumowanie o nowe wydarzenia i stan. Użyj gęstego, telegraficznego skrótu."
						  f" Usuń prozę i dialogi. Skup się na faktach dających kontekst w historii."
						  f" Użyj bezpośredniej, sprośnej (ale nie wulgarnej) terminologii przy opisie ciała."
						  f" Użyj następującego formatu:\n"
						  f" (historia: \n"
						  f"stan emocjonalny: \n"
						  f"stan ciała: )\n"
						  f"Bieżące podsumowanie: {session.get('summary', '')}\n\n"
						  f"Nowe zdarzenia: {text_to_compress}")

				response = self.client.models.generate_content(
					model='gemini-3.5-flash',
					contents=prompt
				)

				if getattr(response, 'usage_metadata', None):
					self.usage_tracker.add_token_usage(
						response.usage_metadata.prompt_token_count,
						response.usage_metadata.candidates_token_count
					)

				if response.text:
					session["summary"] = response.text
					session["summarized_index"] = end_idx
					self.save_history()
			except Exception:
				pass
			finally:
				self.is_compressing = False

		threading.Thread(target=task, daemon=True).start()

	def _init_chat_object(self) -> None:
		caps = self.config.get_model_caps(self.config.current_model)
		self.usage_tracker.max_rpm = caps["max_rpm"]
		self.usage_tracker.max_tpm = caps["max_tpm"]

		safety_settings = [
			types.SafetySetting(category=cat, threshold=types.HarmBlockThreshold.OFF)
			for cat in [
				types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
				types.HarmCategory.HARM_CATEGORY_HARASSMENT,
				types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
				types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
				types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
			]
		]

		config_kwargs = {
			"temperature": self.config.temperature,
			"top_p": self.config.top_p,
			"top_k": self.config.top_k,
			"max_output_tokens": self.config.max_tokens,
			"thinking_config": {"thinking_level": self.config.thinking_level},
			"safety_settings": safety_settings
		}

		if caps["penalties"]:
			config_kwargs["presence_penalty"] = self.config.presence_penalty
			config_kwargs["frequency_penalty"] = self.config.frequency_penalty

		session_data = self.chat_sessions[self.current_session_id]

		if session_data["type"] == "roleplay":
			c = session_data["config"]
			config_kwargs["system_instruction"] = (
				f"AI Config: {c['ai_config']}\n"
				f"Personality: {c['personality']}\n"
				f"Appearance: {c['appearance']}\n"
				f"Context: {c['context']}\n"
				f"Summary: {session_data.get('summary', '')}"
			)
			history_source = session_data["history"][-6:]

			if session_data.get("summarized_index", 1) <= 1:
				if session_data["history"] and session_data["history"][0] not in history_source:
					history_source.insert(0, session_data["history"][0])
		else:
			history_source = session_data["history"]

		valid_history = []
		for msg in history_source:
			if msg["role"] == "ai" and str(msg["content"]).startswith("[API Error:"):
				if valid_history and valid_history[-1]["role"] == "user":
					valid_history.pop()
				continue
			valid_history.append(msg)

		formatted_history = [
			{"role": "user" if msg["role"] == "user" else "model", "parts": [{"text": str(msg["content"])}]}
			for msg in valid_history
		]

		self.active_chat = self.client.chats.create(
			model=self.config.current_model,
			config=types.GenerateContentConfig(**config_kwargs),
			history=formatted_history
		)

	def send_message(self, text: str, callback: Callable[[Optional[str], Optional[str]], None]) -> None:
		if not self.usage_tracker.can_request(self.config.is_paid_tier):
			callback(None, f"Rate Limit Exceeded. Please wait a moment. (Max {self.usage_tracker.max_rpm} RPM)")
			return

		self.usage_tracker.add_request_timestamp()

		def task() -> None:
			try:
				response = self.active_chat.send_message(text)

				if getattr(response, 'usage_metadata', None):
					self.usage_tracker.add_token_usage(
						response.usage_metadata.prompt_token_count,
						response.usage_metadata.candidates_token_count
					)

				if response.text:
					response_text = Formatter.format_quotes(response.text)
				else:
					finish_reason = getattr(response.candidates[0], 'finish_reason', "UNKNOWN") if getattr(response,
																										   'candidates',
																										   None) else "UNKNOWN"
					response_text = f"[API Error: Empty Response. Finish Reason: {finish_reason}]"

				self._record_interaction(text, response_text)
				callback(response_text, None)

			except Exception as e:
				self._record_interaction(text, f"[API Error: {str(e)}]")
				callback(None, str(e))

		threading.Thread(target=task, daemon=True).start()

	def _record_interaction(self, user_text: str, ai_text: str) -> None:
		history = self.chat_sessions[self.current_session_id]["history"]
		history.extend([
			{"role": "user", "content": user_text},
			{"role": "ai", "content": ai_text}
		])
		self.save_history()
		self.compress_history(self.current_session_id)


class ChatUI:
	def __init__(self, gemini_manager: GeminiManager) -> None:
		self.manager = gemini_manager
		self.config = self.manager.config
		self.theme = Theme()

		self.font_family = "Lexend"
		self.font_size = 12

		self.polish_map = {
			'¹': 'ą', 'æ': 'ć', 'ê': 'ę', '³': 'ł', 'ñ': 'ń', 'œ': 'ś', 'Ÿ': 'ź', '\x9f': 'ź', '¿': 'ż',
			'¥': 'Ą', 'Æ': 'Ć', 'Ê': 'Ę', '£': 'Ł', 'Ñ': 'Ń', 'Œ': 'Ś', '\x8f': 'Ź', '¯': 'Ż'
		}

		self.root = tk.Tk()
		self.is_loading = False
		self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
		self.spinner_idx = 0

		self._drag_data = {"x": 0, "y": 0}
		self._resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}

		self._setup_window()
		self._build_layout()
		self.apply_fonts()
		self._bind_events()

		self.refresh_chat_display()
		self.refresh_history_list()
		self.update_usage_display()

	def _setup_window(self) -> None:
		self.root.title("Raccoon Chat")

		try:
			self.root.iconbitmap(default=resource_path("SourceFiles/9-1.ico"))
		except tk.TclError:
			pass

		self.root.overrideredirect(True)
		self.root.attributes("-alpha", 1.0)

		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()
		window_width = int(screen_width * 0.6)
		window_height = int(screen_height * 0.6)
		center_x = int((screen_width - window_width) / 2)
		center_y = int((screen_height - window_height) / 2)

		self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
		self.root.configure(bg=self.theme.bg_main)
		self.root.after(100, self._force_taskbar_icon)

	def _force_taskbar_icon(self) -> None:
		self.root.update_idletasks()
		user32 = ctypes.windll.user32

		user32.GetParent.restype = ctypes.c_void_p
		user32.GetParent.argtypes = [ctypes.c_void_p]

		GetWindowLong = user32.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.GetWindowLongW
		SetWindowLong = user32.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else user32.SetWindowLongW

		GetWindowLong.restype = ctypes.c_void_p
		GetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int]
		SetWindowLong.restype = ctypes.c_void_p
		SetWindowLong.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

		hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()

		GWL_EXSTYLE = -20
		WS_EX_APPWINDOW = 0x00040000
		WS_EX_TOOLWINDOW = 0x00000080

		style = GetWindowLong(hwnd, GWL_EXSTYLE)
		if style is not None:
			style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
			SetWindowLong(hwnd, GWL_EXSTYLE, style)

		self.root.withdraw()
		self.root.deiconify()
		self.root.focus_force()

	def _build_layout(self) -> None:
		self.main_frame = tk.Frame(self.root, bg=self.theme.bg_main, padx=2, pady=2)
		self.main_frame.pack(fill=tk.BOTH, expand=True)

		self._build_top_bar()

		self.content_panes = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL, bg=self.theme.bg_main, bd=0,
											sashwidth=4)
		self.content_panes.pack(fill=tk.BOTH, expand=True, pady=2)

		self._build_sidebar()
		self._build_chat_area()

		self.sizegrip = ttk.Sizegrip(self.main_frame)
		self.sizegrip.place(relx=1.0, rely=1.0, anchor="se")

	def _build_top_bar(self) -> None:
		self.top_bar = tk.Frame(self.main_frame, bg=self.theme.bg_panel, height=30)
		self.top_bar.pack(fill=tk.X, side=tk.TOP)
		self.stats_label = tk.Label(self.top_bar, text="", bg=self.theme.bg_panel, fg=self.theme.fg_muted,
									font=(self.font_family, 9))
		self.stats_label.pack(side=tk.RIGHT, padx=10)

	def _build_sidebar(self) -> None:
		self.sidebar = tk.Frame(self.content_panes, bg=self.theme.bg_panel, width=200)
		self.content_panes.add(self.sidebar)
		self.sidebar_visible = True

		self.btn_frame = tk.Frame(self.sidebar, bg=self.theme.bg_panel)
		self.btn_frame.pack(side=tk.TOP, fill=tk.X)

		self.new_chat_btn = tk.Button(self.btn_frame, text="+ New Chat", bg=self.theme.bg_input,
									  fg=self.theme.fg_accent, bd=0, command=self.show_new_chat_menu)
		self.new_chat_btn.pack(fill=tk.X, padx=5, pady=2)

		self.rename_chat_btn = tk.Button(self.btn_frame, text="* Rename Chat", bg=self.theme.bg_input,
										 fg=self.theme.fg_accent, bd=0, command=self.rename_chat_dialog)
		self.rename_chat_btn.pack(fill=tk.X, padx=5, pady=2)

		self.delete_chat_btn = tk.Button(self.btn_frame, text="- Delete Chat", bg=self.theme.bg_input,
										 fg=self.theme.fg_accent, bd=0, command=self.delete_chat)
		self.delete_chat_btn.pack(fill=tk.X, padx=5, pady=2)

		self.settings_frame = tk.Frame(self.sidebar, bg=self.theme.bg_panel)
		self.settings_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

		self.rp_settings_btn = tk.Button(self.settings_frame, text="RP Settings", bg=self.theme.bg_input,
										 fg=self.theme.fg_accent, bd=0, command=lambda: self.open_rp_setup(False))

		self.open_settings_btn = tk.Button(self.settings_frame, text="Settings (Ctrl+P)", bg=self.theme.bg_input,
										   fg=self.theme.fg_accent, bd=0, command=self.open_settings_dialog)
		self.open_settings_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

		self.separator = tk.Frame(self.sidebar, bg=self.theme.bg_separator, height=2)
		self.separator.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

		self.history_listbox = tk.Listbox(self.sidebar, bg=self.theme.bg_panel, fg=self.theme.fg_accent, bd=0,
										  highlightthickness=0)
		self.history_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)

	def _build_chat_area(self) -> None:
		self.chat_area = tk.Frame(self.content_panes, bg=self.theme.bg_panel)
		self.content_panes.add(self.chat_area)

		self.input_frame = tk.Frame(self.chat_area, bg=self.theme.bg_panel)
		self.input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

		self.input_box = tk.Text(self.input_frame, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
								 highlightthickness=0, height=3)
		self.input_box.pack(fill=tk.BOTH, expand=True)

		self.action_btn_frame = tk.Frame(self.input_box, bg=self.theme.bg_input)

		self.retry_btn = tk.Button(self.action_btn_frame, text="Retry", bg=self.theme.bg_button,
								   fg=self.theme.fg_accent, bd=0, command=self.retry_last_message)
		self.retry_btn.pack(side=tk.RIGHT, padx=5, pady=5)

		self.edit_ai_btn = tk.Button(self.action_btn_frame, text="Edit AI", bg=self.theme.bg_button,
									 fg=self.theme.fg_accent, bd=0, command=lambda: self.edit_last_message_dialog("ai"))
		self.edit_ai_btn.pack(side=tk.RIGHT, padx=5, pady=5)

		self.edit_user_btn = tk.Button(self.action_btn_frame, text="Edit User", bg=self.theme.bg_button,
									   fg=self.theme.fg_accent, bd=0,
									   command=lambda: self.edit_last_message_dialog("user"))
		self.edit_user_btn.pack(side=tk.RIGHT, padx=5, pady=5)

		self.text_display = tk.Text(self.chat_area, bg=self.theme.bg_panel, fg=self.theme.fg_accent, bd=0,
									highlightthickness=0, wrap=tk.WORD)
		self.text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
		self.text_display.tag_configure("user", justify="right", foreground=self.theme.fg_text)
		self.text_display.tag_configure("ai", justify="left", foreground=self.theme.fg_accent)
		self.text_display.tag_configure("ai_loading", justify="left", foreground=self.theme.fg_accent)
		self.text_display.config(state=tk.DISABLED)

	def _safe_shortcut(self, func: Callable) -> Callable:
		def wrapper(event: Any) -> str | None:
			if getattr(event, 'state', 0) & 131072:
				return None
			func(event)
			return "break"

		return wrapper

	def apply_fonts(self) -> None:
		font_tuple = (self.font_family, self.font_size)
		bold_font = (self.font_family, self.font_size, "bold")
		italic_font = (self.font_family, self.font_size, "italic")

		for widget in [self.text_display, self.input_box, getattr(self, 'current_edit_box', None)]:
			if widget and widget.winfo_exists():
				widget.configure(font=font_tuple)
				widget.tag_configure("bold", font=bold_font)
				widget.tag_configure("italic", font=italic_font)
				widget.tag_configure("green", foreground=self.theme.fg_green)
				widget.tag_configure("grey", foreground=self.theme.fg_grey)

				for tag in ["bold", "italic", "green", "grey"]:
					widget.tag_raise(tag)

		self.history_listbox.configure(font=font_tuple)
		self.root.after(10, self.adjust_input_height)
		self.root.after(10, self.apply_live_formatting)

	def apply_live_formatting(self, event: Any = None) -> None:
		widgets = [event.widget] if event and getattr(event, "widget", None) and isinstance(event.widget,
																							tk.Text) else [
			self.input_box]

		if getattr(self, 'current_edit_box',
				   None) and self.current_edit_box.winfo_exists() and self.current_edit_box not in widgets:
			widgets.append(self.current_edit_box)

		for w in widgets:
			for tag in ["bold", "italic", "green", "grey"]:
				w.tag_remove(tag, "1.0", tk.END)

			content = w.get("1.0", "end-1c")
			for match in re.finditer(r'(#[^\n]*|\*\*.*?\*\*|\*.*?\*|"[^"]*?")', content, re.DOTALL):
				start_tk = w.index(f"1.0 + {match.start()} chars")
				end_tk = w.index(f"1.0 + {match.end()} chars")
				matched_text = match.group(0)

				if matched_text.startswith('#'):
					w.tag_add("grey", start_tk, end_tk)
				elif matched_text.startswith('**'):
					w.tag_add("bold", start_tk, end_tk)
				elif matched_text.startswith('"'):
					w.tag_add("green", start_tk, end_tk)
				elif matched_text.startswith('*'):
					w.tag_add("italic", start_tk, end_tk)

	def update_usage_display(self) -> None:
		compress_tag = " [SUMMARIZING...]" if self.manager.is_compressing else ""
		color = self.theme.fg_accent if self.manager.is_compressing else self.theme.fg_muted

		if self.config.is_paid_tier:
			caps = self.config.get_model_caps(self.config.current_model)
			in_tokens = self.manager.usage_tracker.session_input_tokens
			out_tokens = self.manager.usage_tracker.session_output_tokens

			cost_usd = (in_tokens / 1000000 * caps["cost_in"]) + (out_tokens / 1000000 * caps["cost_out"])
			cost_pln = cost_usd * 3.75
			self.stats_label.config(text=f"Session Cost: {cost_pln:.5f} PLN{compress_tag}", fg=color)
		else:
			rpm, tpm = self.manager.usage_tracker.get_stats()
			max_rpm = self.manager.usage_tracker.max_rpm
			max_tpm = self.manager.usage_tracker.max_tpm

			tpm_display = f"{tpm / 1000:.1f}k" if tpm > 1000 else str(tpm)
			max_tpm_display = f"{max_tpm / 1000000:.1f}M" if max_tpm >= 1000000 else f"{max_tpm / 1000:.0f}k"
			self.stats_label.config(text=f"RPM: {rpm}/{max_rpm} | TPM: {tpm_display}/{max_tpm_display}{compress_tag}",
									fg=color)

		self.root.after(1000, self.update_usage_display)

	def intercept_polish_chars(self, event: Any) -> str | None:
		if not event.char:
			return None

		widget = event.widget
		if event.char in self.polish_map or (
				event.char in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ" and getattr(event, 'state', 0) & 131072):
			char_to_insert = self.polish_map.get(event.char, event.char)
			widget.insert(tk.INSERT, char_to_insert)

			if widget == self.input_box:
				self.adjust_input_height()
				self.check_button_visibility()
			self.apply_live_formatting(event)
			return "break"

		return None

	def delete_word(self, event: Any = None) -> str:
		try:
			self.input_box.delete(tk.SEL_FIRST, tk.SEL_LAST)
		except tk.TclError:
			text_before_cursor = self.input_box.get("1.0", tk.INSERT)
			match = re.search(r'(\s+$|\S+)$', text_before_cursor)
			if match:
				self.input_box.delete(f"insert - {len(match.group(1))} chars", tk.INSERT)

		self.adjust_input_height()
		self.check_button_visibility()
		self.apply_live_formatting()
		return "break"

	def zoom_in(self, event: Any = None) -> str:
		self.font_size += 1
		self.apply_fonts()
		return "break"

	def zoom_out(self, event: Any = None) -> str:
		if self.font_size > 6:
			self.font_size -= 1
			self.apply_fonts()
		return "break"

	def zoom_scroll(self, event: Any) -> str:
		if event.delta > 0:
			self.zoom_in()
		else:
			self.zoom_out()
		return "break"

	def _bind_events(self) -> None:
		self.top_bar.bind("<ButtonPress-1>", self.start_drag)
		self.top_bar.bind("<B1-Motion>", self.do_drag)

		for key in ("<Control-q>", "<Control-Q>"):
			self.root.bind(key, self._safe_shortcut(lambda e: self.root.quit()))

		for key in ("<Control-l>", "<Control-L>"):
			self.root.bind(key, self._safe_shortcut(self.toggle_sidebar))

		for key in ("<Control-p>", "<Control-P>"):
			self.root.bind(key, self._safe_shortcut(self.open_settings_dialog))

		self.root.bind("<Control-plus>", self.zoom_in)
		self.root.bind("<Control-equal>", self.zoom_in)
		self.root.bind("<Control-minus>", self.zoom_out)
		self.root.bind("<Control-MouseWheel>", self.zoom_scroll)

		self.sizegrip.bind("<ButtonPress-1>", self.start_resize)
		self.sizegrip.bind("<B1-Motion>", self.do_resize)

		self.input_box.bind("<KeyPress>", self.intercept_polish_chars)
		self.input_box.bind("<Return>", self.send_message_event)
		self.input_box.bind("<Shift-Return>", self.insert_newline)
		self.input_box.bind("<<Paste>>", self.handle_paste)
		self.input_box.bind("<KeyRelease>", self.on_key_release)
		self.input_box.bind("<Motion>", self.check_button_visibility)
		self.input_box.bind("<Leave>", self.on_input_leave)
		self.input_box.bind("<Control-BackSpace>", self.delete_word)

		for w in (self.action_btn_frame, self.retry_btn, self.edit_ai_btn, self.edit_user_btn):
			w.bind("<Motion>", self.check_button_visibility)
			w.bind("<Leave>", self.on_input_leave)

	def start_drag(self, event: Any) -> None:
		self._drag_data.update({"x": event.x, "y": event.y})

	def do_drag(self, event: Any) -> None:
		x = self.root.winfo_x() - self._drag_data["x"] + event.x
		y = self.root.winfo_y() - self._drag_data["y"] + event.y
		self.root.geometry(f"+{x}+{y}")

	def start_resize(self, event: Any) -> None:
		self._resize_data.update({
			"x": event.x_root,
			"y": event.y_root,
			"width": self.root.winfo_width(),
			"height": self.root.winfo_height()
		})

	def do_resize(self, event: Any) -> None:
		new_width = max(600, self._resize_data["width"] + (event.x_root - self._resize_data["x"]))
		new_height = max(400, self._resize_data["height"] + (event.y_root - self._resize_data["y"]))
		self.root.geometry(f"{new_width}x{new_height}")

	def toggle_sidebar(self, event: Any = None) -> None:
		if self.sidebar_visible:
			self.content_panes.forget(self.sidebar)
		else:
			self.content_panes.add(self.sidebar, before=self.chat_area)
		self.sidebar_visible = not self.sidebar_visible

	def refresh_history_list(self) -> None:
		self.history_listbox.delete(0, tk.END)
		for sid in self.manager.chat_sessions.keys():
			self.history_listbox.insert(tk.END, sid)

	def on_history_select(self, event: Any) -> None:
		selection = self.history_listbox.curselection()
		if selection:
			self.manager.switch_session(self.history_listbox.get(selection[0]))
			self.refresh_chat_display()

	def show_new_chat_menu(self) -> None:
		menu = tk.Menu(self.root, tearoff=0, bg=self.theme.bg_panel, fg=self.theme.fg_accent, bd=0)
		menu.add_command(label="Normal Chat", command=self.new_chat)
		menu.add_command(label="Roleplay Chat", command=lambda: self.open_rp_setup(True))
		x = self.new_chat_btn.winfo_rootx()
		y = self.new_chat_btn.winfo_rooty() + self.new_chat_btn.winfo_height()
		menu.tk_popup(x, y)

	def new_chat(self) -> None:
		self.manager.create_new_session()
		self.refresh_history_list()
		self.refresh_chat_display()

	def delete_chat(self) -> None:
		selection = self.history_listbox.curselection()
		sid = self.history_listbox.get(selection[0]) if selection else self.manager.current_session_id
		if sid:
			self.manager.delete_session(sid)
			self.refresh_history_list()
			self.refresh_chat_display()

	def rename_chat_dialog(self) -> None:
		selection = self.history_listbox.curselection()
		if not selection:
			return

		old_id = self.history_listbox.get(selection[0])
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		popup.geometry(f"300x100+{self.root.winfo_x() + 300}+{self.root.winfo_y() + 250}")
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		entry = tk.Entry(popup, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
						 font=(self.font_family, self.font_size))
		entry.pack(fill=tk.X, padx=10, pady=35)
		entry.insert(0, old_id)
		entry.focus_set()

		def confirm(event: Any = None) -> None:
			new_id = entry.get().strip()
			if new_id and new_id != old_id:
				self.manager.rename_session(old_id, new_id)
				self.refresh_history_list()
			popup.destroy()

		entry.bind("<Return>", confirm)
		entry.bind("<Escape>", lambda e: popup.destroy())

	def edit_last_message_dialog(self, role_to_edit: str) -> None:
		session = self.manager.chat_sessions.get(self.manager.current_session_id, {}).get("history", [])
		target_idx = next((i for i in range(len(session) - 1, -1, -1) if session[i]["role"] == role_to_edit), -1)

		if target_idx == -1:
			return

		old_text = session[target_idx]["content"]
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		popup.geometry(f"600x400+{self.root.winfo_x() + 150}+{self.root.winfo_y() + 100}")
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		btn_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

		self.current_edit_box = tk.Text(popup, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
										font=(self.font_family, self.font_size), wrap=tk.WORD)
		self.current_edit_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		self.current_edit_box.insert(1.0, old_text)
		self.current_edit_box.focus_set()

		def save_edit(event: Any = None) -> str:
			new_text = self.current_edit_box.get(1.0, tk.END).strip()
			if new_text:
				session[target_idx]["content"] = new_text
				self.manager.save_history()
				self.manager._init_chat_object()
				self.refresh_chat_display()
			popup.destroy()
			return "break"

		tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				  command=save_edit).pack(side=tk.RIGHT, padx=10)
		tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				  command=popup.destroy).pack(side=tk.RIGHT, padx=5)

		popup.bind("<Escape>", lambda e: popup.destroy())
		self.current_edit_box.bind("<Shift-Return>", save_edit)
		self.current_edit_box.bind("<KeyPress>", self.intercept_polish_chars)
		self.current_edit_box.bind("<KeyRelease>", self.apply_live_formatting)
		self.apply_fonts()

	def open_rp_setup(self, is_new: bool = False) -> None:
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		popup.geometry(f"900x800+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 20}")
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		tk.Label(popup, text="Roleplay Configuration", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
				 font=(self.font_family, self.font_size, "bold")).pack(pady=10)

		main_container = tk.Frame(popup, bg=self.theme.bg_panel)
		main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

		canvas = tk.Canvas(main_container, bg=self.theme.bg_panel, highlightthickness=0)
		scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
		container = tk.Frame(canvas, bg=self.theme.bg_panel)

		container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
		canvas_frame = canvas.create_window((0, 0), window=container, anchor="nw")
		canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
		canvas.configure(yscrollcommand=scrollbar.set)

		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		popup.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

		boxes = {}
		fields = [
			("ai_config", "AI Config"),
			("personality", "Personality"),
			("appearance", "Physical Appearance"),
			("context", "Context"),
			("first_message", "First Message"),
			("summary", "Current Background Summary (Editable)")
		]

		session_data = self.manager.chat_sessions.get(self.manager.current_session_id, {}) if not is_new else {}
		existing_config = session_data.get("config", {})
		existing_summary = session_data.get("summary", "")

		for key, label_text in fields:
			tk.Label(container, text=label_text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
					 font=(self.font_family, self.font_size, "bold")).pack(anchor="w", pady=(5, 0))
			t_box = tk.Text(container, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
							font=(self.font_family, self.font_size), height=6 if key == "summary" else 4, wrap=tk.WORD)
			t_box.pack(fill=tk.X, expand=False, pady=2)

			if key == "summary":
				t_box.insert(1.0, existing_summary)
			elif key in existing_config:
				t_box.insert(1.0, existing_config[key])

			t_box.bind("<KeyPress>", self.intercept_polish_chars)
			t_box.bind("<KeyRelease>", self.apply_live_formatting)
			t_box.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
			boxes[key] = t_box

			if not is_new and key == "first_message":
				t_box.config(state=tk.DISABLED, bg=self.theme.bg_separator)

		btn_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)

		def save_rp_config() -> None:
			configs = {k: box.get(1.0, tk.END).strip() for k, box in boxes.items() if k != "summary"}
			summary_text = boxes["summary"].get(1.0, tk.END).strip()

			if is_new:
				self.manager.create_rp_session(configs)
				self.manager.chat_sessions[self.manager.current_session_id]["summary"] = summary_text
				self.refresh_history_list()
			else:
				session_obj = self.manager.chat_sessions[self.manager.current_session_id]
				configs["first_message"] = existing_config.get("first_message", "")
				session_obj["config"] = configs
				session_obj["summary"] = summary_text
				self.manager.save_history()
				self.manager._init_chat_object()

			self.refresh_chat_display()
			popup.destroy()

		tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0, command=save_rp_config,
				  width=10).pack(side=tk.RIGHT, padx=20)
		tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				  command=popup.destroy, width=10).pack(side=tk.RIGHT, padx=5)
		popup.bind("<Escape>", lambda e: popup.destroy())

	def open_settings_dialog(self, event: Any = None) -> None:
		if getattr(self, 'settings_popup', None) and self.settings_popup.winfo_exists():
			self.settings_popup.focus_set()
			return

		self.settings_popup = tk.Toplevel(self.root)
		self.settings_popup.overrideredirect(True)
		self.settings_popup.geometry(f"400x600+{self.root.winfo_x() + 250}+{self.root.winfo_y() + 50}")
		self.settings_popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		self.settings_popup.attributes("-topmost", True)

		tk.Label(self.settings_popup, text="Model Settings", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
				 font=(self.font_family, self.font_size, "bold")).pack(pady=10)
		container = tk.Frame(self.settings_popup, bg=self.theme.bg_panel)
		container.pack(fill=tk.BOTH, expand=True, padx=20)

		def make_label(text: str, row: int) -> None:
			tk.Label(container, text=text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
					 font=(self.font_family, self.font_size)).grid(row=row, column=0, sticky="w", pady=5)

		make_label("Model:", 0)
		model_var = tk.StringVar(value=self.config.current_model)
		model_cb = ttk.Combobox(container, textvariable=model_var, values=self.config.models, state="readonly")
		model_cb.grid(row=0, column=1, sticky="ew", pady=5)

		def make_scale(row: int, from_: float, to: float, res: float, val: float) -> tk.Scale:
			s = tk.Scale(container, from_=from_, to=to, resolution=res, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
						 fg=self.theme.fg_accent, bd=0, highlightthickness=0)
			s.set(val)
			s.grid(row=row, column=1, sticky="ew", pady=5)
			return s

		temp_scale = make_scale(1, 0.0, 2.0, 0.1, self.config.temperature)
		top_p_scale = make_scale(2, 0.0, 1.0, 0.01, self.config.top_p)
		top_k_scale = make_scale(3, 1, 100, 1, self.config.top_k)
		max_tok_scale = make_scale(4, 1, 8192, 1, self.config.max_tokens)
		pres_scale = make_scale(5, -2.0, 2.0, 0.1, self.config.presence_penalty)
		freq_scale = make_scale(6, -2.0, 2.0, 0.1, self.config.frequency_penalty)

		make_label("Temperature:", 1)
		make_label("Top P:", 2)
		make_label("Top K:", 3)
		make_label("Max Tokens:", 4)
		make_label("Presence Penalty:", 5)
		make_label("Freq Penalty:", 6)
		make_label("Thinking Level:", 7)

		think_var = tk.StringVar(value=self.config.thinking_level)
		think_cb = ttk.Combobox(container, textvariable=think_var, values=self.config.thinking_levels, state="readonly")
		think_cb.grid(row=7, column=1, sticky="ew", pady=5)

		paid_tier_var = tk.BooleanVar(value=self.config.is_paid_tier)
		paid_tier_cb = tk.Checkbutton(container, text="Paid Account (Hide RPM, Track Cost)", variable=paid_tier_var,
									  bg=self.theme.bg_panel, fg=self.theme.fg_text, selectcolor=self.theme.bg_input,
									  activebackground=self.theme.bg_panel, activeforeground=self.theme.fg_text)
		paid_tier_cb.grid(row=8, column=0, columnspan=2, sticky="w", pady=10)

		def update_dynamic_limits(event: Any = None) -> None:
			caps = self.config.get_model_caps(model_var.get())
			max_tok_scale.config(to=caps["max_tokens"])
			if max_tok_scale.get() > caps["max_tokens"]:
				max_tok_scale.set(caps["max_tokens"])

			state, color = (tk.NORMAL, self.theme.fg_accent) if caps["penalties"] else (tk.DISABLED,
																						self.theme.fg_muted)
			pres_scale.config(state=state, fg=color)
			freq_scale.config(state=state, fg=color)

		model_cb.bind("<<ComboboxSelected>>", update_dynamic_limits)
		update_dynamic_limits()

		btn_frame = tk.Frame(self.settings_popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)

		def save_settings() -> None:
			self.config.current_model = model_var.get()
			self.config.temperature = temp_scale.get()
			self.config.top_p = top_p_scale.get()
			self.config.top_k = int(top_k_scale.get())
			self.config.max_tokens = int(max_tok_scale.get())
			self.config.presence_penalty = pres_scale.get()
			self.config.frequency_penalty = freq_scale.get()
			self.config.thinking_level = think_var.get()
			self.config.is_paid_tier = paid_tier_var.get()
			self.manager._init_chat_object()
			self.settings_popup.destroy()
			self.update_usage_display()

		tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0, command=save_settings,
				  width=10).pack(side=tk.RIGHT, padx=20)
		tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				  command=self.settings_popup.destroy, width=10).pack(side=tk.RIGHT, padx=5)
		self.settings_popup.bind("<Escape>", lambda e: self.settings_popup.destroy())

	def start_loading(self) -> None:
		self.is_loading = True
		self.text_display.config(state=tk.NORMAL)
		self.text_display.insert(tk.END, "⠋ Thinking...\n\n", "ai_loading")
		self.text_display.see(tk.END)
		self.text_display.config(state=tk.DISABLED)
		self.animate_spinner()

	def animate_spinner(self) -> None:
		if not self.is_loading:
			return

		self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)
		self.text_display.config(state=tk.NORMAL)
		ranges = self.text_display.tag_ranges("ai_loading")

		if ranges:
			self.text_display.delete(ranges[0], ranges[1])
			self.text_display.insert(ranges[0], f"{self.spinner_frames[self.spinner_idx]} Thinking...", "ai_loading")

		self.text_display.config(state=tk.DISABLED)
		self.root.after(100, self.animate_spinner)

	def stop_loading(self) -> None:
		self.is_loading = False
		self.text_display.config(state=tk.NORMAL)
		ranges = self.text_display.tag_ranges("ai_loading")

		if ranges:
			self.text_display.delete(ranges[0], tk.END)

		self.text_display.config(state=tk.DISABLED)

	def on_key_release(self, event: Any = None) -> None:
		self.adjust_input_height()
		self.check_button_visibility()
		self.apply_live_formatting(event)

	def check_button_visibility(self, event: Any = None) -> None:
		if self.is_loading or self.input_box.get("1.0", "end-1c").strip():
			self.hide_action_buttons()
			return

		try:
			x, y = self.root.winfo_pointerxy()
			widget = self.root.winfo_containing(x, y)
		except KeyError:
			self.hide_action_buttons()
			return

		is_in_buttons = widget in (self.action_btn_frame, self.retry_btn, self.edit_ai_btn, self.edit_user_btn)
		is_in_hover_zone = widget == self.input_box and (
					x - self.input_box.winfo_rootx() > self.input_box.winfo_width() - 200)

		if is_in_buttons or is_in_hover_zone:
			self.show_action_buttons()
		else:
			self.hide_action_buttons()

	def on_input_leave(self, event: Any = None) -> None:
		try:
			x, y = self.root.winfo_pointerxy()
			widget = self.root.winfo_containing(x, y)
			if widget not in (self.action_btn_frame, self.retry_btn, self.edit_ai_btn, self.edit_user_btn):
				self.hide_action_buttons()
		except KeyError:
			self.hide_action_buttons()

	def show_action_buttons(self) -> None:
		if not self.action_btn_frame.winfo_ismapped():
			self.action_btn_frame.place(relx=1.0, rely=1.0, x=-5, y=-5, anchor="se")

	def hide_action_buttons(self) -> None:
		if self.action_btn_frame.winfo_ismapped():
			self.action_btn_frame.place_forget()

	def adjust_input_height(self, event: Any = None) -> None:
		chat_area_h = self.chat_area.winfo_height()
		if chat_area_h <= 10:
			return

		lines_tuple = self.input_box.count("1.0", "end", "displaylines")
		actual_lines = max(1, lines_tuple[0] if lines_tuple else 1)

		current_font = tkfont.Font(font=self.input_box.cget("font"))
		max_lines = max(3, int((chat_area_h * 0.8) / current_font.metrics("linespace")))
		target_lines = max(3, min(actual_lines, max_lines))

		if float(self.input_box.cget("height")) != target_lines:
			self.input_box.configure(height=target_lines)

	def send_message_event(self, event: Any) -> str:
		text = self.input_box.get(1.0, tk.END).strip()
		if not text:
			return "break"

		self.input_box.delete(1.0, tk.END)
		self.input_box.configure(height=3)
		self.hide_action_buttons()
		self.append_message("user", text)
		self.start_loading()
		self.manager.send_message(text, self.receive_message)
		return "break"

	def retry_last_message(self) -> None:
		session = self.manager.chat_sessions.get(self.manager.current_session_id, {}).get("history", [])
		if len(session) >= 2 and session[-1]["role"] == "ai" and session[-2]["role"] == "user":
			user_text = session[-2]["content"]
			self.manager.chat_sessions[self.manager.current_session_id]["history"] = session[:-2]
			self.manager._init_chat_object()
			self.refresh_chat_display()
			self.append_message("user", user_text)
			self.start_loading()
			self.manager.send_message(user_text, self.receive_message)

	def insert_newline(self, event: Any) -> str:
		self.input_box.insert(tk.INSERT, "\n")
		self.adjust_input_height()
		self.check_button_visibility()
		return "break"

	def handle_paste(self, event: Any) -> str:
		try:
			event.widget.insert(tk.INSERT, self.root.clipboard_get())
			if event.widget == self.input_box:
				self.root.after(10, self.adjust_input_height)
				self.hide_action_buttons()
			self.root.after(10, lambda: self.apply_live_formatting(event))
		except tk.TclError:
			pass
		return "break"

	def receive_message(self, text: Optional[str], error: Optional[str]) -> None:
		self.stop_loading()
		self.append_message("ai", f"Error: {error}" if error else text)

	def insert_formatted(self, widget: tk.Text, text: str, base_tag: str) -> None:
		for part in re.split(r'(#[^\n]*|\*\*.*?\*\*|\*.*?\*|"[^"]*?")', text):
			if part.startswith('#'):
				widget.insert(tk.END, part, (base_tag, "grey"))
			elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
				widget.insert(tk.END, part[2:-2], (base_tag, "bold"))
			elif part.startswith('"') and part.endswith('"') and len(part) >= 2:
				widget.insert(tk.END, part, (base_tag, "green"))
			elif part.startswith('*') and part.endswith('*') and len(part) >= 2:
				widget.insert(tk.END, part[1:-1], (base_tag, "italic"))
			else:
				widget.insert(tk.END, part, (base_tag,))

	def append_message(self, role: str, text: str) -> None:
		self.text_display.config(state=tk.NORMAL)
		self.insert_formatted(self.text_display, str(text), role)
		self.text_display.insert(tk.END, "\n\n", role)
		self.text_display.see(tk.END)
		self.text_display.config(state=tk.DISABLED)

	def refresh_chat_display(self) -> None:
		self.text_display.config(state=tk.NORMAL)
		self.text_display.delete(1.0, tk.END)

		session_data = self.manager.chat_sessions.get(self.manager.current_session_id, {})
		if not session_data:
			self.text_display.config(state=tk.DISABLED)
			return

		history = session_data.get("history", [])
		sum_idx = session_data.get("summarized_index", -1)

		for i, msg in enumerate(history):
			if session_data.get("type") == "roleplay" and i == sum_idx:
				self.insert_formatted(self.text_display, "# --- Memory Compressed Above This Line ---\n\n", "ai")
			self.insert_formatted(self.text_display, str(msg["content"]), msg["role"])
			self.text_display.insert(tk.END, "\n\n", msg["role"])

		if session_data.get("type") == "roleplay":
			self.rp_settings_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=2, before=self.open_settings_btn)
		else:
			self.rp_settings_btn.pack_forget()

		self.text_display.see(tk.END)
		self.text_display.config(state=tk.DISABLED)

	def run(self) -> None:
		self.root.mainloop()


if __name__ == "__main__":
	ui = ChatUI(GeminiManager(AppConfig()))
	ui.run()