import sys
import os
import json
import time
import ctypes
import re
import locale
import threading
import ctypes.wintypes
import colorsys
import tkinter as tk
from contextlib import suppress
from tkinter import ttk, font as tkfont, filedialog, colorchooser
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from spellchecker import SpellChecker

from PIL import Image, ImageTk
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



class DarkColorPicker(tk.Toplevel):
	def __init__(self, parent, theme: 'Theme', initial_color: str = "#ffffff", title: str = "Pick Color"):
		super().__init__(parent)
		self.theme = theme
		self.title(title)
		self.resizable(False, False)
		self.transient(parent)
		self.grab_set()
		self.configure(bg=theme.bg_panel)
		self.current_color = initial_color
		if not self.current_color.startswith("#"):
			self.current_color = "#ffffff"
		self.result = None
		self.h, self.s, self.v = self._hex_to_hsv(self.current_color)
		self._build_ui()
		self._update_color_display()
		self.update_idletasks()
		x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
		y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
		self.geometry(f"+{x}+{y}")
		self.protocol("WM_DELETE_WINDOW", self._on_cancel)

	def _hex_to_hsv(self, hex_color):
		hex_color = hex_color.lstrip('#')
		r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
		return colorsys.rgb_to_hsv(r, g, b)

	def _hsv_to_hex(self, h, s, v):
		r, g, b = colorsys.hsv_to_rgb(h, s, v)
		return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))

	def _build_ui(self):
		main_frame = tk.Frame(self, bg=self.theme.bg_panel, padx=20, pady=20)
		main_frame.pack()
		self.sat_val_canvas = tk.Canvas(main_frame, width=200, height=200, bg="black", highlightthickness=0)
		self.sat_val_canvas.grid(row=0, column=0, padx=(0, 10))
		self.sat_val_canvas.bind("<B1-Motion>", self._on_sat_val_click)
		self.sat_val_canvas.bind("<Button-1>", self._on_sat_val_click)
		self.hue_canvas = tk.Canvas(main_frame, width=20, height=200, bg="black", highlightthickness=0)
		self.hue_canvas.grid(row=0, column=1)
		self.hue_canvas.bind("<B1-Motion>", self._on_hue_click)
		self.hue_canvas.bind("<Button-1>", self._on_hue_click)
		self._draw_hue_gradient()
		self._draw_sat_val_gradient()
		bottom_frame = tk.Frame(main_frame, bg=self.theme.bg_panel, pady=20)
		bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
		tk.Label(bottom_frame, text="HEX:", bg=self.theme.bg_panel, fg=self.theme.fg_text).pack(side=tk.LEFT)
		self.hex_var = tk.StringVar(value=self.current_color)
		self.hex_entry = tk.Entry(bottom_frame, textvariable=self.hex_var, width=10, 
		                         bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0)
		self.hex_entry.pack(side=tk.LEFT, padx=10)
		self.hex_var.trace_add("write", self._on_hex_entry_change)
		self.preview_label = tk.Label(bottom_frame, width=10, height=2, bg=self.current_color)
		self.preview_label.pack(side=tk.RIGHT)
		btn_frame = tk.Frame(self, bg=self.theme.bg_panel, pady=10)
		btn_frame.pack(fill=tk.X)
		tk.Button(btn_frame, text="Cancel", command=self._on_cancel, 
		          bg=self.theme.bg_button, fg=self.theme.fg_text, bd=0, padx=15).pack(side=tk.RIGHT, padx=20)
		tk.Button(btn_frame, text="OK", command=self._on_ok, 
		          bg=self.theme.bg_button, fg=self.theme.fg_accent, bd=0, padx=20).pack(side=tk.RIGHT)

	def _draw_hue_gradient(self):
		self.hue_canvas.delete("gradient")
		for y in range(200):
			h = y / 200.0
			color = self._hsv_to_hex(h, 1.0, 1.0)
			self.hue_canvas.create_line(0, y, 20, y, fill=color, tags="gradient")
		self.hue_indicator = self.hue_canvas.create_line(0, self.h * 200, 20, self.h * 200, fill="white", width=2)

	def _draw_sat_val_gradient(self):
		self.sat_val_canvas.delete("gradient")
		for x in range(0, 200, 4):
			for y in range(0, 200, 4):
				s = x / 200.0
				v = 1.0 - (y / 200.0)
				color = self._hsv_to_hex(self.h, s, v)
				self.sat_val_canvas.create_rectangle(x, y, x+4, y+4, fill=color, outline=color, tags="gradient")
		self.sat_val_indicator = self.sat_val_canvas.create_oval(
			self.s * 200 - 5, (1-self.v) * 200 - 5, 
			self.s * 200 + 5, (1-self.v) * 200 + 5, 
			outline="white", width=2)

	def _on_hue_click(self, event):
		self.h = max(0, min(199, event.y)) / 200.0
		self.hue_canvas.coords(self.hue_indicator, 0, self.h * 200, 20, self.h * 200)
		self._draw_sat_val_gradient()
		self._update_color_display()

	def _on_sat_val_click(self, event):
		self.s = max(0, min(200, event.x)) / 200.0
		self.v = 1.0 - (max(0, min(200, event.y)) / 200.0)
		self.sat_val_canvas.coords(self.sat_val_indicator, 
		                           self.s * 200 - 5, (1-self.v) * 200 - 5, 
		                           self.s * 200 + 5, (1-self.v) * 200 + 5)
		self._update_color_display()

	def _update_color_display(self):
		self.current_color = self._hsv_to_hex(self.h, self.s, self.v)
		self.hex_var.set(self.current_color)
		self.preview_label.configure(bg=self.current_color)

	def _on_hex_entry_change(self, *args):
		hex_val = self.hex_var.get()
		if len(hex_val) == 7 and hex_val.startswith("#"):
			try:
				self.h, self.s, self.v = self._hex_to_hsv(hex_val)
				self.current_color = hex_val
				self.preview_label.configure(bg=self.current_color)
				self.hue_canvas.coords(self.hue_indicator, 0, self.h * 200, 20, self.h * 200)
				self.sat_val_canvas.coords(self.sat_val_indicator, 
				                           self.s * 200 - 5, (1-self.v) * 200 - 5, 
				                           self.s * 200 + 5, (1-self.v) * 200 + 5)
				self._draw_sat_val_gradient()
			except:
				pass

	def _on_ok(self):
		self.result = self.current_color
		self.destroy()

	def _on_cancel(self):
		self.destroy()

	def get_color(self):
		self.wait_window()
		return self.result

@dataclass
class Theme:
	bg_main: str = "#050505"
	bg_panel: str = "#1a1a1a"
	bg_input: str = "#2a2a2a"
	bg_button: str = "#333333"
	bg_separator: str = "#3a3a3a"
	fg_text: str = "#ffffff"
	fg_accent: str = "#ece1f7"
	fg_muted: str = "#888888"
	fg_green: str = "#90ee90"
	fg_grey: str = "#aaaaaa"

	def to_dict(self) -> Dict[str, str]:
		return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

	@classmethod
	def from_dict(cls, data: Dict[str, str]) -> 'Theme':
		return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AppConfig:
	api_key: str = field(init=False)
	history_file: Path = Path("chat_history.json")
	config_file: Path = Path("config.json")
	theme: Theme = field(default_factory=Theme)
	models: List[str] = field(default_factory=lambda: [
		'gemini-3.6-flash',
		'gemini-3.6-flash-lite',
		'gemini-3.5-flash',
		'gemini-3.1-flash-lite',
		'gemini-2.5-flash',
		'gemini-2.0-flash',
		'gemini-2.5-pro'
	])
	current_model: str = 'gemini-3.6-flash'
	temperature: float = 1.3
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
		self.load_config()

	def load_config(self) -> None:
		if self.config_file.exists():
			try:
				data = json.loads(self.config_file.read_text(encoding='utf-8'))
				if "theme" in data:
					self.theme = Theme.from_dict(data["theme"])
				self.current_model = data.get("current_model", self.current_model)
				self.temperature = data.get("temperature", self.temperature)
				self.top_k = data.get("top_k", self.top_k)
				self.top_p = data.get("top_p", self.top_p)
				self.max_tokens = data.get("max_tokens", self.max_tokens)
				self.presence_penalty = data.get("presence_penalty", self.presence_penalty)
				self.frequency_penalty = data.get("frequency_penalty", self.frequency_penalty)
				self.thinking_level = data.get("thinking_level", self.thinking_level)
				self.is_paid_tier = data.get("is_paid_tier", self.is_paid_tier)
			except Exception:
				pass

	def save_config(self) -> None:
		data = {
			"theme": self.theme.to_dict(),
			"current_model": self.current_model,
			"temperature": self.temperature,
			"top_k": self.top_k,
			"top_p": self.top_p,
			"max_tokens": self.max_tokens,
			"presence_penalty": self.presence_penalty,
			"frequency_penalty": self.frequency_penalty,
			"thinking_level": self.thinking_level,
			"is_paid_tier": self.is_paid_tier
		}
		self.config_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

	def get_model_caps(self, model_name: str) -> Dict[str, Any]:
		return {
			"max_tokens": 4096 if "lite" in model_name else 8192,
			"penalties": not any(v in model_name for v in ["3.6", "3.5", "3.1", "2.0"]),
			"max_rpm": 15,
			"max_tpm": 1000000,
			"cost_in": 1.25 if "pro" in model_name else 0.075,
			"cost_out": 5.00 if "pro" in model_name else 0.30,
			"cost_storage_ph": 4.50 if "pro" in model_name else 1.00
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


class SpellCheckerHelper:
	def __init__(self):
		self.spell = SpellChecker()
		# Common profanity to highlight
		self.profanity = {
			"fuck", "shit", "asshole", "bitch", "cunt", "dick", "pussy", 
			"damn", "hell", "bastard", "cock", "faggot", "nigger"
		}
		# Ensure some contractions are known
		self.spell.word_frequency.load_words([
			"aren't", "can't", "couldn't", "didn't", "doesn't", "don't", 
			"hadn't", "hasn't", "haven't", "he'd", "he'll", "he's", 
			"i'd", "i'll", "i'm", "i've", "isn't", "it's", "let's", 
			"mightn't", "mustn't", "shan't", "she'd", "she'll", "she's", 
			"shouldn't", "that's", "there's", "they'd", "they'll", "they're", 
			"they've", "we'd", "we're", "we've", "weren't", "what'll", 
			"what're", "what's", "what've", "where's", "who'd", "who'll", 
			"who're", "who's", "who've", "won't", "wouldn't", "you'd", 
			"you'll", "you're", "you've"
		])

	def is_correct(self, word: str) -> bool:
		if not word: return True
		word_lower = word.lower()
		if word_lower in self.profanity:
			return False
		# pyspellchecker works best with lowercase words
		return word_lower in self.spell or not word.isalpha()

	def suggestions(self, word: str) -> List[str]:
		word_lower = word.lower()
		# Handle common contraction errors manually for better suggestions
		contraction_map = {
			"arent": "aren't", "cant": "can't", "couldnt": "couldn't",
			"didnt": "didn't", "doesnt": "doesn't", "dont": "don't",
			"hadnt": "hadn't", "hasnt": "hasn't", "havent": "haven't",
			"isnt": "isn't", "itll": "it'll", "its": "it's", "shouldnt": "shouldn't",
			"werent": "weren't", "wont": "won't", "wouldnt": "wouldn't",
			"youre": "you're", "theyre": "they're", "were": "we're"
		}
		if word_lower in contraction_map:
			return [contraction_map[word_lower]] + list(self.spell.candidates(word) or [])

		candidates = self.spell.candidates(word)
		return list(candidates) if candidates else []


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
		self.current_cache = None
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
			self._update_context_cache()
			self._init_chat_object()

	def save_history(self) -> None:
		self.config.history_file.write_text(json.dumps(self.chat_sessions, indent=2), encoding='utf-8')

	def create_new_session(self) -> None:
		session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		self.chat_sessions[session_id] = {"type": "normal", "history": []}
		self.current_session_id = session_id
		self._update_context_cache()
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
		self._update_context_cache()
		self._init_chat_object()
		self.save_history()

	def delete_session(self, session_id: str) -> None:
		if session_id in self.chat_sessions:
			del self.chat_sessions[session_id]
			self.save_history()

			if self.current_session_id == session_id:
				if self.chat_sessions:
					self.current_session_id = list(self.chat_sessions.keys())[-1]
					self._update_context_cache()
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
			self._update_context_cache()
			self._init_chat_object()

	def _build_cache_contents(self, session_data: dict) -> str:
		c = session_data["config"]
		return (
			f"AI Config: {c['ai_config']}\n"
			f"Personality: {c['personality']}\n"
			f"Appearance: {c['appearance']}\n"
			f"Context: {c['context']}\n"
			f"Summary: {session_data.get('summary', '')}"
		)

	def _update_context_cache(self) -> None:
		session_data = self.chat_sessions.get(self.current_session_id)
		if not session_data or session_data.get("type") != "roleplay":
			if self.current_cache:
				with suppress(Exception):
					self.client.caches.delete(name=self.current_cache.name)
				self.current_cache = None
			return

		if self.current_cache:
			with suppress(Exception):
				self.client.caches.delete(name=self.current_cache.name)
			self.current_cache = None

		cache_text = self._build_cache_contents(session_data)

		try:
			self.current_cache = self.client.caches.create(
				model=self.config.current_model,
				config=types.CreateContextCacheConfig(
					contents=[cache_text],
					ttl="300s"
				)
			)
		except Exception:
			self.current_cache = None

	def get_cache_stats(self) -> dict:
		session = self.chat_sessions.get(self.current_session_id, {})
		is_rp = session.get("type") == "roleplay"

		if not is_rp or not self.current_cache:
			return {
				"status": "Inactive (Normal Chat or Text Too Short)",
				"tokens": 0,
				"expires": "N/A",
				"cost_ph": 0.0
			}

		text = self._build_cache_contents(session)
		estimated_tokens = len(text) // 4

		caps = self.config.get_model_caps(self.config.current_model)
		cost_usd_ph = (estimated_tokens / 1000000) * caps.get("cost_storage_ph", 1.0)
		cost_pln_ph = cost_usd_ph * 3.75

		return {
			"status": f"Active ({self.current_cache.name})",
			"tokens": estimated_tokens,
			"expires": "5 minutes (Refreshes on prompt)",
			"cost_ph": cost_pln_ph
		}

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
					model='gemini-3.6-flash',
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
					self._update_context_cache()
					self._init_chat_object()
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
			if self.current_cache:
				config_kwargs["cached_content"] = self.current_cache.name
				history_source = session_data["history"][-6:]
			else:
				config_kwargs["system_instruction"] = self._build_cache_contents(session_data)
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

		if self.current_cache:
			with suppress(Exception):
				self.client.caches.update(
					name=self.current_cache.name,
					config=types.UpdateContextCacheConfig(ttl="300s")
				)

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
		if not self.current_session_id:
			return
		history = self.chat_sessions[self.current_session_id]["history"]
		history.extend([
			{"role": "user", "content": user_text},
			{"role": "ai", "content": ai_text}
		])
		self.save_history()
		self.compress_history(self.current_session_id)


class GlobalHotkey(threading.Thread):
	def __init__(self, callback: Callable[[], None]) -> None:
		super().__init__(daemon=True)
		self.callback = callback

	def run(self) -> None:
		user32 = ctypes.windll.user32
		MOD_CONTROL = 0x0002
		VK_OEM_3 = 0xC0
		HOTKEY_ID = 101

		if user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL, VK_OEM_3):
			msg = ctypes.wintypes.MSG()
			while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
				if msg.message == 0x0312:
					self.callback()
			user32.UnregisterHotKey(None, HOTKEY_ID)


class ChatUI:
	def __init__(self, gemini_manager: GeminiManager) -> None:
		self.manager = gemini_manager
		self.config = self.manager.config
		self.theme = self.config.theme

		self.font_family = "Lexend"
		self.font_size = 12
		self.is_app_hidden = False

		self.avatar_size = 64
		self.user_avatar_path = None
		self.ai_avatar_path = None
		self.user_avatar_tk = None
		self.ai_avatar_tk = None

		self.sidebar_visible = True
		self.current_edit_box = None
		self.settings_popup = None

		self.polish_map = {
			'¹': 'ą', 'æ': 'ć', 'ê': 'ę', '³': 'ł', 'ñ': 'ń', 'œ': 'ś', 'Ÿ': 'ź', '\x9f': 'ź', '¿': 'ż',
			'¥': 'Ą', 'Æ': 'Ć', 'Ê': 'Ę', '£': 'Ł', 'Ñ': 'Ń', 'Œ': 'Ś', '\x8f': 'Ź', '¯': 'Ż'
		}

		self.root = tk.Tk()
		self.is_loading = False
		self.spell_checker = SpellCheckerHelper()
		self.spell_after_id = None
		self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
		self.spinner_idx = 0

		self._drag_data = {"x": 0, "y": 0}
		self._resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}

		self.image_panel_visible = False
		self.current_image = None
		self.current_photo = None

		self._setup_window()
		self._build_layout()
		self.apply_fonts()
		self._bind_events()

		self.hotkey_thread = GlobalHotkey(self.trigger_toggle_from_thread)
		self.hotkey_thread.start()

		self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

		self.refresh_chat_display()
		self.refresh_history_list()
		self.update_usage_display()

	def trigger_toggle_from_thread(self) -> None:
		self.root.after(0, self.toggle_app_visibility)

	def toggle_app_visibility(self, _: Any = None) -> str:
		if self.is_app_hidden:
			self.root.deiconify()
			self.root.focus_force()
			self.is_app_hidden = False
		else:
			self.root.withdraw()
			self.is_app_hidden = True
		return "break"

	def on_app_close(self) -> None:
		self.config.save_config()
		if self.manager.current_cache:
			cache_name = self.manager.current_cache.name
			threading.Thread(
				target=lambda: suppress(Exception)(self.manager.client.caches.delete(name=cache_name)),
				daemon=False
			).start()
		self.root.destroy()

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
		self._build_image_panel()

		self.sizegrip = ttk.Sizegrip(self.main_frame)
		self.sizegrip.place(relx=1.0, rely=1.0, anchor=tk.SE)

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

		self.toggle_img_panel_btn = tk.Button(self.btn_frame, text="Toggle Img Panel", bg=self.theme.bg_input,
		                                      fg=self.theme.fg_accent, bd=0, command=self.toggle_image_panel)
		self.toggle_img_panel_btn.pack(fill=tk.X, padx=5, pady=2)

		self.settings_frame = tk.Frame(self.sidebar, bg=self.theme.bg_panel)
		self.settings_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

		self.rp_settings_btn = tk.Button(self.settings_frame, text="RP Settings", bg=self.theme.bg_input,
		                                 fg=self.theme.fg_accent, bd=0, command=lambda: self.open_rp_setup(False))

		self.overview_btn = tk.Button(self.settings_frame, text="Overview", bg=self.theme.bg_input,
		                               fg=self.theme.fg_accent, bd=0, command=self.open_overview_dialog)

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
		self.text_display.tag_configure("user", justify="right", foreground=self.theme.fg_text, spacing3=4)
		self.text_display.tag_configure("ai", justify="left", foreground=self.theme.fg_accent, spacing3=4)
		self.text_display.tag_configure("ai_loading", justify="left", foreground=self.theme.fg_accent, spacing3=4)
		self.text_display.tag_configure("green", foreground=self.theme.fg_green)
		self.text_display.tag_configure("grey", foreground=self.theme.fg_grey)
		self.input_box.tag_configure("misspelled", underline=True)
		self.text_display.config(state=tk.DISABLED)

	def _build_image_panel(self) -> None:
		self.image_panel = tk.Frame(self.content_panes, bg=self.theme.bg_panel, width=250)

		self.avatar_btn = tk.Button(self.image_panel, text="Pick Avatars", bg=self.theme.bg_input,
		                            fg=self.theme.fg_accent, bd=0, command=self.pick_avatars)
		self.avatar_btn.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

		self.img_btn_frame = tk.Frame(self.image_panel, bg=self.theme.bg_panel)
		self.img_btn_frame.pack(side=tk.TOP, fill=tk.X)

		self.upload_btn = tk.Button(self.img_btn_frame, text="Upload Image", bg=self.theme.bg_input,
		                            fg=self.theme.fg_accent, bd=0, command=self.upload_image)
		self.upload_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 2), pady=5)

		self.clear_btn = tk.Button(self.img_btn_frame, text="X", bg=self.theme.bg_input,
		                           fg=self.theme.fg_accent, bd=0, command=self.clear_image)
		self.clear_btn.pack(side=tk.RIGHT, padx=(2, 5), pady=5)

		self.image_canvas = tk.Canvas(self.image_panel, bg=self.theme.bg_panel, bd=0, highlightthickness=0)
		self.image_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		self.image_canvas.bind("<Configure>", self.resize_image)

	def pick_avatars(self) -> None:
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		self.center_window(popup, 300, 160)
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, popup))
		popup.bind("<B1-Motion>", lambda e: self.do_drag(e, popup))

		def pick_user():
			path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
			if path:
				self.user_avatar_path = path
				if self.manager.current_session_id in self.manager.chat_sessions:
					self.manager.chat_sessions[self.manager.current_session_id]["user_avatar"] = path
					self.manager.save_history()
				self.load_avatars()
				self.refresh_chat_display()

		def pick_ai():
			path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
			if path:
				self.ai_avatar_path = path
				if self.manager.current_session_id in self.manager.chat_sessions:
					self.manager.chat_sessions[self.manager.current_session_id]["ai_avatar"] = path
					self.manager.save_history()
				self.load_avatars()
				self.refresh_chat_display()

		tk.Button(popup, text="Pick User Avatar", bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
		          command=pick_user).pack(fill=tk.X, padx=10, pady=(15, 5))
		tk.Button(popup, text="Pick AI Avatar", bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
		          command=pick_ai).pack(fill=tk.X, padx=10, pady=5)
		tk.Button(popup, text="Close", bg=self.theme.bg_button, fg=self.theme.fg_accent, bd=0,
		          command=popup.destroy).pack(fill=tk.X, padx=10, pady=(15, 10))

	def load_avatars(self) -> None:
		scaled_size = max(10, int(self.avatar_size * (self.font_size / 12.0)))
		if self.user_avatar_path and os.path.exists(self.user_avatar_path):
			try:
				img = Image.open(self.user_avatar_path).resize((scaled_size, scaled_size), Image.Resampling.LANCZOS)
				self.user_avatar_tk = ImageTk.PhotoImage(img)
			except Exception:
				self.user_avatar_tk = None
		else:
			self.user_avatar_tk = None

		if self.ai_avatar_path and os.path.exists(self.ai_avatar_path):
			try:
				img = Image.open(self.ai_avatar_path).resize((scaled_size, scaled_size), Image.Resampling.LANCZOS)
				self.ai_avatar_tk = ImageTk.PhotoImage(img)
			except Exception:
				self.ai_avatar_tk = None
		else:
			self.ai_avatar_tk = None

	@staticmethod
	def _safe_shortcut(func: Callable) -> Callable:
		def wrapper(event: Any) -> str | None:
			if getattr(event, 'state', 0) & 131072:
				return None
			func(event)
			return "break"

		return wrapper

	def toggle_image_panel(self, _: Any = None) -> None:
		if self.image_panel_visible:
			self.content_panes.forget(self.image_panel)
		else:
			self.content_panes.add(self.image_panel)
		self.image_panel_visible = not self.image_panel_visible

	def upload_image(self) -> None:
		if not self.manager.current_session_id:
			return
		file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
		if file_path:
			self.manager.chat_sessions[self.manager.current_session_id]["image_path"] = file_path
			self.manager.save_history()
			self._load_session_image()

	def clear_image(self) -> None:
		if not self.manager.current_session_id:
			return
		session = self.manager.chat_sessions.get(self.manager.current_session_id, {})
		if "image_path" in session:
			del session["image_path"]
			self.manager.save_history()
		self.current_image = None
		self.image_canvas.delete("all")

	def _load_session_image(self) -> None:
		session = self.manager.chat_sessions.get(self.manager.current_session_id, {})
		image_path = session.get("image_path")
		if image_path and os.path.exists(image_path):
			try:
				self.current_image = Image.open(image_path)
				self.display_image()
			except Exception:
				self.current_image = None
				self.image_canvas.delete("all")
		else:
			self.current_image = None
			self.image_canvas.delete("all")

	def resize_image(self, _: Any = None) -> None:
		if not self.current_image:
			return
		self.display_image()

	def display_image(self) -> None:
		if not self.current_image:
			return
		canvas_w = self.image_canvas.winfo_width()
		canvas_h = self.image_canvas.winfo_height()
		if canvas_w < 10 or canvas_h < 10:
			return
		img_w, img_h = self.current_image.size
		ratio = min(canvas_w / img_w, canvas_h / img_h)
		new_w, new_h = int(img_w * ratio), int(img_h * ratio)
		if new_w <= 0 or new_h <= 0:
			return
		resized_img = self.current_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
		self.current_photo = ImageTk.PhotoImage(resized_img)
		self.image_canvas.delete("all")
		self.image_canvas.create_image(canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=self.current_photo)

	def apply_theme(self) -> None:
		self.root.configure(bg=self.theme.bg_main)

		widgets_to_update = [
			(self.sidebar, "bg_panel"),
			(self.top_bar, "bg_panel"),
			(self.content_panes, "bg_panel"),
			(self.chat_area, "bg_panel"),
			(self.input_frame, "bg_panel"),
			(self.image_panel, "bg_panel"),
			(self.img_btn_frame, "bg_panel"),
			(self.action_btn_frame, "bg_input"),
			(self.settings_frame, "bg_panel"),
			(self.separator, "bg_separator"),
			(self.new_chat_btn, "bg_input", "fg_accent"),
			(self.toggle_img_panel_btn, "bg_input", "fg_accent"),
			(self.rp_settings_btn, "bg_input", "fg_accent"),
			(self.overview_btn, "bg_input", "fg_accent"),
			(self.open_settings_btn, "bg_input", "fg_accent"),
			(self.history_listbox, "bg_panel", "fg_accent"),
			(self.input_box, "bg_input", "fg_text"),
			(self.retry_btn, "bg_button", "fg_accent"),
			(self.edit_ai_btn, "bg_button", "fg_accent"),
			(self.edit_user_btn, "bg_button", "fg_accent"),
			(self.text_display, "bg_panel", "fg_accent"),
			(self.avatar_btn, "bg_input", "fg_accent"),
			(self.upload_btn, "bg_input", "fg_accent"),
			(self.clear_btn, "bg_input", "fg_accent"),
			(self.image_canvas, "bg_panel"),
			(self.main_frame, "bg_main"),
			(self.stats_label, "bg_panel", "fg_muted"),
			(self.rename_chat_btn, "bg_input", "fg_accent"),
			(self.delete_chat_btn, "bg_input", "fg_accent"),
			(self.content_panes, "bg_main")
		]

		for item in widgets_to_update:
			widget = item[0]
			if widget and widget.winfo_exists():
				bg_color = getattr(self.theme, item[1])
				widget.configure(bg=bg_color)
				if len(item) > 2:
					fg_color = getattr(self.theme, item[2])
					widget.configure(fg=fg_color)

		if self.text_display.winfo_exists():
			self.text_display.tag_configure("user", foreground=self.theme.fg_text, spacing3=4)
			self.text_display.tag_configure("ai", foreground=self.theme.fg_accent, spacing3=4)
			self.text_display.tag_configure("ai_loading", foreground=self.theme.fg_accent, spacing3=4)
			self.text_display.tag_configure("green", foreground=self.theme.fg_green)
			self.text_display.tag_configure("grey", foreground=self.theme.fg_grey)

	def apply_fonts(self) -> None:
		self.apply_theme()
		font_tuple = (self.font_family, self.font_size)
		bold_font = (self.font_family, self.font_size, "bold")
		italic_font = (self.font_family, self.font_size, "italic")

		for widget in [self.text_display, self.input_box, self.current_edit_box]:
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
		widgets = [event.widget] if event and isinstance(getattr(event, "widget", None), tk.Text) else [self.input_box]

		if self.current_edit_box and self.current_edit_box.winfo_exists() and self.current_edit_box not in widgets:
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
		widget = event.widget if event is not None else self.input_box
		# If a selection exists, remove it
		try:
			widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
		except tk.TclError:
			# No selection — delete previous whole word
			if isinstance(widget, tk.Text):
				text_before_cursor = widget.get("1.0", tk.INSERT)
				match = re.search(r'(\s+$|\S+)$', text_before_cursor)
				if match:
					widget.delete(f"insert - {len(match.group(1))} chars", tk.INSERT)
			else:
				# Entry-like widgets (tk.Entry, ttk.Entry)
				try:
					idx = int(widget.index(tk.INSERT))
				except Exception:
					idx = None
				if not idx:
					return "break"
				text = widget.get()
				left = text[:idx]
				match = re.search(r'(\s+$|\S+)$', left)
				if match:
					start = idx - len(match.group(1))
					widget.delete(start, tk.INSERT)

		# If this was the main input box, keep UI in sync
		if widget == self.input_box:
			self.adjust_input_height()
			self.check_button_visibility()
			self.apply_live_formatting()
		return "break"

	def zoom_in(self, _: Any = None) -> str:
		self.font_size += 1
		self.apply_fonts()
		self.load_avatars()
		self.refresh_chat_display()
		return "break"

	def zoom_out(self, _: Any = None) -> str:
		if self.font_size > 6:
			self.font_size -= 1
			self.apply_fonts()
			self.load_avatars()
			self.refresh_chat_display()
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

		self.root.bind("<Control-grave>", self.toggle_app_visibility)

		for key in ("<Control-q>", "<Control-Q>"):
			self.root.bind(key, self._safe_shortcut(lambda e: self.root.quit()))

		for key in ("<Control-l>", "<Control-L>"):
			self.root.bind(key, self._safe_shortcut(self.toggle_sidebar))

		for key in ("<Control-i>", "<Control-I>"):
			self.root.bind(key, self._safe_shortcut(self.toggle_image_panel))

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
		self.input_box.bind("<Button-1>", lambda e: self.show_spell_menu(e, self.input_box))
		self.input_box.bind("<Motion>", self.check_button_visibility)
		self.input_box.bind("<Leave>", self.on_input_leave)
		self.input_box.bind("<Control-BackSpace>", self.delete_word)
		# Bind Ctrl+BackSpace for all Entry (tk and ttk) and Text widgets so every text input
		# gains the standard whole-word delete behavior.
		for cls in ("Entry", "TEntry", "Text"):
			try:
				self.root.bind_class(cls, "<Control-BackSpace>", self._safe_shortcut(self.delete_word))
			except Exception:
				pass

		for w in (self.action_btn_frame, self.retry_btn, self.edit_ai_btn, self.edit_user_btn):
			w.bind("<Motion>", self.check_button_visibility)
			w.bind("<Leave>", self.on_input_leave)

	def _bind_scroll(self, widget: tk.Widget, canvas: tk.Canvas) -> None:
		widget.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"), add="+")
		for child in widget.winfo_children():
			self._bind_scroll(child, canvas)

	def center_window(self, window: tk.Toplevel, width: int, height: int) -> None:
		screen_width = window.winfo_screenwidth()
		screen_height = window.winfo_screenheight()
		x = (screen_width // 2) - (width // 2)
		y = (screen_height // 2) - (height // 2)
		window.geometry(f"{width}x{height}+{x}+{y}")

	def start_drag(self, event: Any, window: Optional[tk.Toplevel] = None) -> None:
		if isinstance(event.widget, (tk.Text, tk.Entry, tk.Scale, tk.Canvas, ttk.Combobox)):
			return
		self._drag_data.update({"x": event.x, "y": event.y})

	def do_drag(self, event: Any, window: Optional[tk.Toplevel] = None) -> None:
		if isinstance(event.widget, (tk.Text, tk.Entry, tk.Scale, tk.Canvas, ttk.Combobox)):
			return
		target = window if window else self.root
		x = target.winfo_x() - self._drag_data["x"] + event.x
		y = target.winfo_y() - self._drag_data["y"] + event.y
		target.geometry(f"+{x}+{y}")

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

	def toggle_sidebar(self, _: Any = None) -> None:
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
		self.center_window(popup, 300, 100)
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, popup))
		popup.bind("<B1-Motion>", lambda e: self.do_drag(e, popup))

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
		self.center_window(popup, 600, 400)
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, popup))
		popup.bind("<B1-Motion>", lambda e: self.do_drag(e, popup))

		btn_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

		self.current_edit_box = tk.Text(popup, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
		                                font=(self.font_family, self.font_size), wrap=tk.WORD)
		self.current_edit_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		self.current_edit_box.tag_configure("misspelled", underline=True)
		self.current_edit_box.insert(1.0, old_text)
		self.current_edit_box.focus_set()
		self.check_spelling(self.current_edit_box)

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
		self.current_edit_box.bind("<KeyRelease>", lambda e: (self.apply_live_formatting(e), self.debounce_spell_check(self.current_edit_box)))
		self.current_edit_box.bind("<Button-1>", lambda e: self.show_spell_menu(e, self.current_edit_box))
		self.apply_fonts()

	def open_rp_setup(self, is_new: bool = False, auto_edit_first: bool = False) -> None:
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		self.center_window(popup, 1000, 900)
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, popup))
		popup.bind("<B1-Motion>", lambda e: self.do_drag(e, popup))

		tk.Label(popup, text="Roleplay Configuration", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
		         font=(self.font_family, self.font_size, "bold")).pack(pady=10)

		main_container = tk.Frame(popup, bg=self.theme.bg_panel)
		main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

		session_data = self.manager.chat_sessions.get(self.manager.current_session_id, {}) if not is_new else {}
		existing_config = session_data.get("config", {})
		existing_summary = session_data.get("summary", "")

		field_data = {
			"ai_config": existing_config.get("ai_config", ""),
			"personality": existing_config.get("personality", ""),
			"appearance": existing_config.get("appearance", ""),
			"context": existing_config.get("context", ""),
			"first_message": existing_config.get("first_message", ""),
		}

		fields = [
			("ai_config", "AI Config"),
			("personality", "Personality"),
			("appearance", "Physical Appearance"),
			("context", "Context"),
			("first_message", "First Message")
		]

		preview_labels = {}

		def open_edit_window(key, label_text):
			edit_popup = tk.Toplevel(popup)
			edit_popup.overrideredirect(True)
			self.center_window(edit_popup, 800, 600)
			edit_popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
			edit_popup.attributes("-topmost", True)

			edit_popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, edit_popup))
			edit_popup.bind("<B1-Motion>", lambda e: self.do_drag(e, edit_popup))

			tk.Label(edit_popup, text=f"Edit {label_text}", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
			         font=(self.font_family, self.font_size, "bold")).pack(pady=10)

			btn_frame = tk.Frame(edit_popup, bg=self.theme.bg_panel)
			btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)

			t_box = tk.Text(edit_popup, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
			                font=(self.font_family, self.font_size), wrap=tk.WORD, undo=True)
			t_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
			t_box.tag_configure("misspelled", underline=True)
			t_box.insert(1.0, field_data[key])
			t_box.focus_set()
			self.check_spelling(t_box)

			t_box.bind("<KeyPress>", self.intercept_polish_chars)
			t_box.bind("<KeyRelease>", lambda e: (self.apply_live_formatting(e), self.debounce_spell_check(t_box)))
			t_box.bind("<Button-1>", lambda e: self.show_spell_menu(e, t_box))

			def save_field():
				new_val = t_box.get(1.0, tk.END).strip()
				field_data[key] = new_val
				# Update preview
				preview_text = (new_val[:150] + "...") if len(new_val) > 150 else new_val
				if not preview_text: preview_text = "(Empty)"
				preview_labels[key].config(text=preview_text)
				edit_popup.destroy()

			tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
			          command=save_field, width=15, height=2).pack(side=tk.RIGHT, padx=20)
			tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
			          command=edit_popup.destroy, width=15, height=2).pack(side=tk.RIGHT, padx=5)
			
			edit_popup.bind("<Escape>", lambda e: edit_popup.destroy())
			t_box.bind("<Shift-Return>", lambda e: save_field())

		# Top part: Previews and Edit buttons
		preview_container = tk.Frame(main_container, bg=self.theme.bg_panel)
		preview_container.pack(fill=tk.X)

		for i, (key, label_text) in enumerate(fields):
			row = i // 2
			col = i % 2
			
			f_frame = tk.Frame(preview_container, bg=self.theme.bg_panel, bd=1, relief=tk.RIDGE)
			f_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
			preview_container.grid_columnconfigure(col, weight=1)

			header_frame = tk.Frame(f_frame, bg=self.theme.bg_panel)
			header_frame.pack(fill=tk.X, padx=5, pady=2)
			
			tk.Label(header_frame, text=label_text, bg=self.theme.bg_panel, fg=self.theme.fg_accent,
			         font=(self.font_family, self.font_size, "bold")).pack(side=tk.LEFT)
			
			is_locked = not is_new and key == "first_message" and field_data[key] and not auto_edit_first
			
			if not is_locked:
				tk.Button(header_frame, text="Edit", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				          command=lambda k=key, l=label_text: open_edit_window(k, l), padx=10).pack(side=tk.RIGHT)
			else:
				def unlock_first_message():
					from tkinter import messagebox
					if messagebox.askyesno("Unlock First Message", "Unlocking will delete all chat history after the first message. Continue?"):
						session_obj = self.manager.chat_sessions[self.manager.current_session_id]
						if len(session_obj["history"]) > 1:
							session_obj["history"] = session_obj["history"][:1]
							self.manager.save_history()
						
						# Refresh popup and automatically open edit window
						popup.destroy()
						self.open_rp_setup(False, auto_edit_first=True)

				tk.Button(header_frame, text="Unlock", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
				          command=unlock_first_message, padx=10).pack(side=tk.RIGHT)
				tk.Label(header_frame, text="(Locked)", bg=self.theme.bg_panel, fg=self.theme.fg_muted,
				         font=(self.font_family, self.font_size - 2)).pack(side=tk.RIGHT)

			val = field_data[key]
			preview_text = (val[:150] + "...") if len(val) > 150 else val
			if not preview_text: preview_text = "(Empty)"
			
			lbl = tk.Label(f_frame, text=preview_text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
			               font=(self.font_family, self.font_size - 1), justify=tk.LEFT, anchor="nw", wraplength=450)
			lbl.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
			preview_labels[key] = lbl

		if auto_edit_first:
			open_edit_window("first_message", "First Message")

		# Bottom part: Summary field (directly editable)
		summary_header = tk.Frame(main_container, bg=self.theme.bg_panel)
		summary_header.pack(fill=tk.X, pady=(15, 0))

		tk.Label(summary_header, text="Current Background Summary (Editable)", bg=self.theme.bg_panel, fg=self.theme.fg_text,
		         font=(self.font_family, self.font_size, "bold")).pack(side=tk.LEFT)

		tk.Button(summary_header, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
		          command=lambda: save_rp_config(), padx=10).pack(side=tk.RIGHT)
		tk.Button(summary_header, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
		          command=popup.destroy, padx=10).pack(side=tk.RIGHT, padx=5)

		summary_box = tk.Text(main_container, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0,
		                    font=(self.font_family, self.font_size), height=10, wrap=tk.WORD, undo=True)
		summary_box.pack(fill=tk.BOTH, expand=True, pady=5)
		summary_box.tag_configure("misspelled", underline=True)
		summary_box.insert(1.0, existing_summary)
		summary_box.bind("<KeyPress>", self.intercept_polish_chars)
		summary_box.bind("<KeyRelease>", lambda e: (self.apply_live_formatting(e), self.debounce_spell_check(summary_box)))
		summary_box.bind("<Button-1>", lambda e: self.show_spell_menu(e, summary_box))
		self.check_spelling(summary_box)

		def save_rp_config() -> None:
			configs = {k: v for k, v in field_data.items()}
			summary_text = summary_box.get(1.0, tk.END).strip()

			if is_new:
				self.manager.create_rp_session(configs)
				self.manager.chat_sessions[self.manager.current_session_id]["summary"] = summary_text
				self.refresh_history_list()
			else:
				session_obj = self.manager.chat_sessions[self.manager.current_session_id]
				# If first_message was locked, it wouldn't have been editable, so it's safe to use field_data[key] 
				# if we correctly update field_data. Actually, if it's locked, we use the existing one.
				# If it was UNLOCKED, it becomes editable and field_data is updated.
				
				# Check if it was locked during this popup session
				was_locked = not is_new and existing_config.get("first_message", "")
				# If it was locked, and it's still "locked" (no unlock button pressed that closed popup),
				# then field_data["first_message"] would be the same as existing_config.
				
				# The logic: if it's editable, the user might have changed it.
				# If it was locked, we didn't show the Edit button.
				
				session_obj["config"] = configs
				session_obj["summary"] = summary_text
				
				# Update history if first message changed
				if session_obj["history"] and session_obj["history"][0]["role"] == "ai":
					session_obj["history"][0]["content"] = configs["first_message"]
				
				self.manager.save_history()
				self.manager._update_context_cache()
				self.manager._init_chat_object()

			self.refresh_chat_display()
			popup.destroy()

		btn_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)

		tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0, command=save_rp_config,
		          padx=10).pack(side=tk.RIGHT, padx=20)
		tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
		          command=popup.destroy, padx=10).pack(side=tk.RIGHT, padx=5)
		popup.bind("<Escape>", lambda e: popup.destroy())

	def open_settings_dialog(self, _: Any = None) -> None:
		from tkinter import colorchooser
		if self.settings_popup and self.settings_popup.winfo_exists():
			self.settings_popup.focus_set()
			return

		self.settings_popup = tk.Toplevel(self.root)
		self.settings_popup.overrideredirect(True)
		self.center_window(self.settings_popup, 850, 850)
		self.settings_popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		self.settings_popup.attributes("-topmost", True)

		self.settings_popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, self.settings_popup))
		self.settings_popup.bind("<B1-Motion>", lambda e: self.do_drag(e, self.settings_popup))

		tk.Label(self.settings_popup, text="Settings", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
		         font=(self.font_family, self.font_size, "bold")).pack(pady=10)

		main_content = tk.Frame(self.settings_popup, bg=self.theme.bg_panel)
		main_content.pack(expand=True, fill=tk.BOTH)

		container = tk.Frame(main_content, bg=self.theme.bg_panel)
		container.place(relx=0.5, rely=0.5, anchor="center")

		container.grid_columnconfigure(0, weight=1)
		container.grid_columnconfigure(1, weight=1)

		# Appearance Settings to the LEFT (column 0)
		appearance_frame = tk.Frame(container, bg=self.theme.bg_panel)
		appearance_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

		tk.Label(appearance_frame, text="Appearance Settings", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
		         font=(self.font_family, self.font_size, "bold")).pack(anchor="w", pady=10)

		color_vars = {}
		for color_name in self.theme.to_dict().keys():
			f = tk.Frame(appearance_frame, bg=self.theme.bg_panel)
			f.pack(fill=tk.X, pady=2)
			tk.Label(f, text=f"{color_name}:", bg=self.theme.bg_panel, fg=self.theme.fg_text,
			         font=(self.font_family, self.font_size)).pack(side=tk.LEFT)
			
			c_var = tk.StringVar(value=getattr(self.theme, color_name))
			color_vars[color_name] = c_var

			c_entry = tk.Entry(f, textvariable=c_var, bg=self.theme.bg_input, fg=self.theme.fg_text, bd=0, width=10)
			c_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

			def pick_color_factory(name, var):
				def pick():
					new_color = DarkColorPicker(self.settings_popup, self.theme, initial_color=var.get(), title=f"Pick {name}").get_color()
					if new_color:
						var.set(new_color)
				return pick

			tk.Button(f, text="Pick", bg=self.theme.bg_button, fg=self.theme.fg_accent, bd=0,
			          command=pick_color_factory(color_name, c_var)).pack(side=tk.RIGHT, padx=5)

		# Model Settings to the RIGHT (column 1)
		model_settings_frame = tk.Frame(container, bg=self.theme.bg_panel)
		model_settings_frame.grid(row=0, column=1, sticky="nsew")

		tk.Label(model_settings_frame, text="Model Settings", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
		         font=(self.font_family, self.font_size, "bold")).pack(anchor="w", pady=10)

		def make_row(parent, label_text):
			f = tk.Frame(parent, bg=self.theme.bg_panel)
			f.pack(fill=tk.X, pady=2)
			tk.Label(f, text=label_text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
			         font=(self.font_family, self.font_size)).pack(side=tk.LEFT)
			return f

		f = make_row(model_settings_frame, "Model:")
		model_var = tk.StringVar(value=self.config.current_model)
		model_cb = ttk.Combobox(f, textvariable=model_var, values=self.config.models, state="readonly")
		model_cb.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

		def make_scale_row(parent, label_text, from_, to, res, val):
			tk.Label(parent, text=label_text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
			         font=(self.font_family, self.font_size)).pack(anchor="w", pady=(5, 0))
			s = tk.Scale(parent, from_=from_, to=to, resolution=res, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
			             fg=self.theme.fg_accent, bd=0, highlightthickness=0)
			s.set(val)
			s.pack(fill=tk.X, pady=(0, 5))
			return s

		temp_scale = make_scale_row(model_settings_frame, "Temperature:", 0.0, 2.0, 0.1, self.config.temperature)
		top_p_scale = make_scale_row(model_settings_frame, "Top P:", 0.0, 1.0, 0.01, self.config.top_p)
		top_k_scale = make_scale_row(model_settings_frame, "Top K:", 1, 100, 1, self.config.top_k)
		max_tok_scale = make_scale_row(model_settings_frame, "Max Tokens:", 1, 8192, 1, self.config.max_tokens)
		pres_scale = make_scale_row(model_settings_frame, "Presence Penalty:", -2.0, 2.0, 0.1, self.config.presence_penalty)
		freq_scale = make_scale_row(model_settings_frame, "Freq Penalty:", -2.0, 2.0, 0.1, self.config.frequency_penalty)

		f = make_row(model_settings_frame, "Thinking Level:")
		think_var = tk.StringVar(value=self.config.thinking_level)
		think_cb = ttk.Combobox(f, textvariable=think_var, values=self.config.thinking_levels, state="readonly")
		think_cb.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

		paid_tier_var = tk.BooleanVar(value=self.config.is_paid_tier)
		paid_tier_cb = tk.Checkbutton(model_settings_frame, text="Paid Account (Hide RPM, Track Cost)", variable=paid_tier_var,
		                              bg=self.theme.bg_panel, fg=self.theme.fg_text, selectcolor=self.theme.bg_input,
		                              activebackground=self.theme.bg_panel, activeforeground=self.theme.fg_text)
		paid_tier_cb.pack(anchor="w", pady=10)

		def update_dynamic_limits(event: Any = None) -> None:
			caps = self.config.get_model_caps(model_var.get())
			max_tok_scale.config(to=caps["max_tokens"])
			if max_tok_scale.get() > caps["max_tokens"]:
				max_tok_scale.set(caps["max_tokens"])

			state, color = (tk.NORMAL, self.theme.fg_accent) if caps["penalties"] else (tk.DISABLED, self.theme.fg_muted)
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

			new_theme_data = {name: var.get() for name, var in color_vars.items()}
			self.config.theme = Theme.from_dict(new_theme_data)
			self.theme = self.config.theme

			self.config.save_config()
			self.apply_fonts() # This calls apply_theme

			self.manager._update_context_cache()
			self.manager._init_chat_object()
			self.settings_popup.destroy()
			self.update_usage_display()

		tk.Button(btn_frame, text="Save", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0, command=save_settings,
		          width=10).pack(side=tk.RIGHT, padx=20)
		tk.Button(btn_frame, text="Cancel", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
		          command=self.settings_popup.destroy, width=10).pack(side=tk.RIGHT, padx=5)
		self.settings_popup.bind("<Escape>", lambda e: self.settings_popup.destroy())

	def open_overview_dialog(self, _: Any = None) -> None:
		popup = tk.Toplevel(self.root)
		popup.overrideredirect(True)
		self.center_window(popup, 400, 250)
		popup.configure(bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		popup.attributes("-topmost", True)

		popup.bind("<ButtonPress-1>", lambda e: self.start_drag(e, popup))
		popup.bind("<B1-Motion>", lambda e: self.do_drag(e, popup))

		tk.Label(popup, text="Context Caching Statistics", bg=self.theme.bg_panel, fg=self.theme.fg_accent,
		         font=(self.font_family, self.font_size, "bold")).pack(pady=10)

		stats_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

		stats = self.manager.get_cache_stats()
		def make_stat_label(text: str):
			tk.Label(stats_frame, text=text, bg=self.theme.bg_panel, fg=self.theme.fg_text,
			         font=(self.font_family, 10)).pack(anchor="w", pady=2)

		make_stat_label(f"Status: {stats['status']}")
		make_stat_label(f"Estimated Tokens: {stats['tokens']:,}")
		make_stat_label(f"Storage Cost: ~{stats['cost_ph']:.4f} PLN / hour")
		make_stat_label(f"Time to Live: {stats['expires']}")

		btn_frame = tk.Frame(popup, bg=self.theme.bg_panel)
		btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=15)

		tk.Button(btn_frame, text="Close", bg=self.theme.bg_input, fg=self.theme.fg_accent, bd=0,
		          command=popup.destroy, width=10).pack(side=tk.RIGHT, padx=20)

		popup.bind("<Escape>", lambda e: popup.destroy())

	def start_loading(self) -> None:
		self.is_loading = True
		self.text_display.config(state=tk.NORMAL)
		self.text_display.insert(tk.END, "⠋ Thinking...\n", "ai_loading")
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
		self.debounce_spell_check(self.input_box)

	def debounce_spell_check(self, widget: tk.Text) -> None:
		if self.spell_after_id:
			self.root.after_cancel(self.spell_after_id)
		self.spell_after_id = self.root.after(500, lambda: self.check_spelling(widget))

	def check_spelling(self, widget: tk.Text) -> None:
		widget.tag_remove("misspelled", "1.0", tk.END)
		text = widget.get("1.0", tk.END)
		
		# regex to isolate words. We allow apostrophes inside words.
		for match in re.finditer(r"\b\w+('\w+)?\b", text):
			word = match.group()
			start_pos = match.start()
			
			is_misspelled = not self.spell_checker.is_correct(word)
			
			# Check for sentence start capitalization
			if not is_misspelled and word[0].islower():
				# Look at characters before the word
				preceding = text[:start_pos].rstrip()
				if not preceding or preceding[-1] in ".!?":
					is_misspelled = True

			if is_misspelled:
				start_idx = f"1.0 + {start_pos} chars"
				end_idx = f"1.0 + {match.end()} chars"
				widget.tag_add("misspelled", start_idx, end_idx)

	def show_spell_menu(self, event: tk.Event, widget: tk.Text) -> str:
		# Convert click position to text index
		idx = widget.index(f"@{event.x},{event.y}")
		
		# Check if the click is on a misspelled word
		tags = widget.tag_names(idx)
		if "misspelled" not in tags:
			return "continue"

		# If it's Button-1, we want to show the menu but NOT interfere with selection if the user is dragging
		# However, simple click is usually what triggers it.
		
		# Find word boundaries
		word_start = widget.index(f"{idx} wordstart")
		word_end = widget.index(f"{idx} wordend")
		word = widget.get(word_start, word_end).strip()
		
		if not word:
			return "continue"

		suggestions = self.spell_checker.suggestions(word)
		
		# For sentence start capitalization errors that are otherwise correct
		if word[0].islower() and self.spell_checker.is_correct(word):
			capitalized = word[0].upper() + word[1:]
			if capitalized not in suggestions:
				suggestions = [capitalized] + suggestions

		menu = tk.Menu(self.root, tearoff=0, bg=self.theme.bg_panel, fg=self.theme.fg_accent, bd=0)
		
		if suggestions:
			for sug in suggestions[:5]: # Limit to top 5 suggestions
				menu.add_command(label=sug, command=lambda s=sug, ws=word_start, we=word_end: self.replace_word(widget, ws, we, s))
		else:
			menu.add_command(label="(No suggestions)", state=tk.DISABLED)
			
		menu.add_separator()
		menu.add_command(label="Add to dictionary", command=lambda w=word: self.add_to_dict(w, widget))

		menu.tk_popup(event.x_root, event.y_root)
		return "break"

	def replace_word(self, widget: tk.Text, start: str, end: str, new_word: str) -> None:
		widget.delete(start, end)
		widget.insert(start, new_word)
		self.check_spelling(widget)

	def add_to_dict(self, word: str, widget: tk.Text) -> None:
		self.spell_checker.spell.word_frequency.add(word.lower())
		self.check_spelling(widget)

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
		if not self.manager.current_session_id:
			return
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

	@staticmethod
	def insert_formatted(widget: tk.Text, text: str, base_tag: str) -> None:
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

		if role == "user" and self.user_avatar_tk:
			self.text_display.insert(tk.END, " ", role)
			self.text_display.image_create(tk.END, image=self.user_avatar_tk)
			self.text_display.insert(tk.END, "\n", role)
		elif role == "ai" and self.ai_avatar_tk:
			self.text_display.image_create(tk.END, image=self.ai_avatar_tk)
			self.text_display.insert(tk.END, "\n", role)

		self.insert_formatted(self.text_display, str(text), role)
		self.text_display.insert(tk.END, "\n", role)
		self.text_display.see(tk.END)
		self.text_display.config(state=tk.DISABLED)

	def refresh_chat_display(self) -> None:
		self.text_display.config(state=tk.NORMAL)
		self.text_display.delete(1.0, tk.END)

		session_data = self.manager.chat_sessions.get(self.manager.current_session_id, {})
		if not session_data:
			self.text_display.config(state=tk.DISABLED)
			return

		self.user_avatar_path = session_data.get("user_avatar")
		self.ai_avatar_path = session_data.get("ai_avatar")
		self.load_avatars()

		history = session_data.get("history", [])
		sum_idx = session_data.get("summarized_index", -1)

		for i, msg in enumerate(history):
			if session_data.get("type") == "roleplay" and i == sum_idx:
				self.insert_formatted(self.text_display, "# --- Memory Compressed Above This Line ---\n", "ai")

			role = msg["role"]
			if role == "user" and self.user_avatar_tk:
				self.text_display.insert(tk.END, " ", role)
				self.text_display.image_create(tk.END, image=self.user_avatar_tk)
				self.text_display.insert(tk.END, "\n", role)
			elif role == "ai" and self.ai_avatar_tk:
				self.text_display.image_create(tk.END, image=self.ai_avatar_tk)
				self.text_display.insert(tk.END, "\n", role)

			self.insert_formatted(self.text_display, str(msg["content"]), role)
			self.text_display.insert(tk.END, "\n", role)

		if session_data.get("type") == "roleplay":
			self.overview_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=2, before=self.open_settings_btn)
			self.rp_settings_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=2, before=self.overview_btn)
		else:
			self.overview_btn.pack_forget()
			self.rp_settings_btn.pack_forget()

		self.text_display.see(tk.END)
		self.text_display.config(state=tk.DISABLED)

		self._load_session_image()

	def run(self) -> None:
		self.root.mainloop()


if __name__ == "__main__":
	ui = ChatUI(GeminiManager(AppConfig()))
	ui.run()