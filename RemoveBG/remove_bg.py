from rembg import remove, new_session
from PIL import Image, ImageTk, ImageFilter
from Raccoon.windowsUtilities import win_files_path
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import os
import sys
import threading

if hasattr(sys, "_MEIPASS"):
	os.environ["U2NET_HOME"] = os.path.join(sys._MEIPASS, "models")


class Theme:
	bg_main: str = "#050505"
	bg_panel: str = "#1a1a1a"
	bg_input: str = "#2a2a2a"
	bg_button: str = "#333333"
	bg_separator: str = "#3a3a3a"
	bg_close: str = "#4a1111"
	bg_close_active: str = "#d12e2e"
	fg_text: str = "#ffffff"
	fg_accent: str = "#d8b4e2"
	fg_muted: str = "#888888"
	fg_green: str = "#90ee90"
	fg_grey: str = "#aaaaaa"


class BackgroundRemoverUI:
	def __init__(self) -> None:
		self.theme = Theme()
		self.font_family = "Lexend"

		self.root = tk.Tk()
		self.root.withdraw()

		raw_paths = win_files_path('Images', 'image')

		if not raw_paths:
			self.root.destroy()
			sys.exit()

		if isinstance(raw_paths, str):
			self.input_paths = [Path(raw_paths)]
		else:
			self.input_paths = [Path(p) for p in raw_paths]

		self.current_index = 0
		self.zoom_level = 1.0
		self.pan_x = 0
		self.pan_y = 0
		self._last_rendered_size = (0, 0)
		self._preview_timer = None
		self._is_processing = False

		self.loaded_sessions = {}
		self.model_map = {
			"General Object (u2net)": "u2net",
			"Anime / 2D Art (isnet-anime)": "isnet-anime",
			"Human Seg (u2net_human_seg)": "u2net_human_seg",
			"Clothing Seg (u2net_cloth_seg)": "u2net_cloth_seg",
			"Lightweight (u2netp)": "u2netp",
			"Ultra Lightweight (silueta)": "silueta",
			"General Object (isnet-general)": "isnet-general-use",
			"Bria RMBG": "bria-rmbg"
		}
		self.root.deiconify()
		self._setup_window()
		self._build_layout()
		self._bind_events()
		self.root.after(200, self._load_current_image)

	def _get_session(self, model_display_name: str):
		model_id = self.model_map[model_display_name]
		if model_display_name not in self.loaded_sessions:
			self.loaded_sessions[model_display_name] = new_session(model_id)
		return self.loaded_sessions[model_display_name]

	def _setup_window(self) -> None:
		self.root.title("Raccoon Background Remover")
		self.root.overrideredirect(True)
		self.root.attributes("-alpha", 1.0)

		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()
		window_width = int(screen_width * 0.55)
		window_height = int(screen_height * 0.75)
		center_x = int((screen_width - window_width) / 2)
		center_y = int((screen_height - window_height) / 2)

		self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
		self.root.configure(bg=self.theme.bg_main)

		self._drag_data = {"x": 0, "y": 0}
		self._resize_data = {"x": 0, "y": 0, "width": 0, "height": 0}
		self._pan_data = {"x": 0, "y": 0}

	def _build_layout(self) -> None:
		self.title_bar = tk.Frame(self.root, bg=self.theme.bg_panel, height=40)
		self.title_bar.pack(fill=tk.X, side=tk.TOP)
		self.title_bar.pack_propagate(False)

		title_label = tk.Label(
			self.title_bar,
			text="RACCOON BACKGROUND REMOVER",
			font=(self.font_family, 10, "bold"),
			bg=self.theme.bg_panel,
			fg=self.theme.fg_accent
		)
		title_label.pack(side=tk.LEFT, padx=15)

		close_button = tk.Button(
			self.title_bar,
			text="✕",
			font=(self.font_family, 11),
			bg=self.theme.bg_close,
			fg=self.theme.fg_text,
			bd=0,
			width=5,
			activebackground=self.theme.bg_close_active,
			activeforeground=self.theme.fg_text,
			command=self.root.destroy,
			cursor="hand2"
		)
		close_button.pack(side=tk.RIGHT, fill=tk.Y)

		self.workspace = tk.Frame(self.root, bg=self.theme.bg_main)
		self.workspace.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

		self.preview_panel = tk.Frame(self.workspace, bg=self.theme.bg_panel, bd=1, relief=tk.SOLID)
		self.preview_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

		self.preview_canvas = tk.Canvas(self.preview_panel, bg=self.theme.bg_panel, highlightthickness=0)
		self.preview_canvas.pack(fill=tk.BOTH, expand=True)

		self.controls_panel = tk.Frame(self.workspace, bg=self.theme.bg_panel, pady=15, padx=15)
		self.controls_panel.pack(fill=tk.X, side=tk.BOTTOM)

		model_label = tk.Label(self.controls_panel, text="AI Processing Model:", font=(self.font_family, 10),
							   bg=self.theme.bg_panel, fg=self.theme.fg_text)
		model_label.grid(row=0, column=0, sticky=tk.W, pady=5)

		self.model_var = tk.StringVar(value="General Object (u2net)")
		self.model_dropdown = ttk.Combobox(self.controls_panel, textvariable=self.model_var,
										   values=list(self.model_map.keys()), state="readonly", width=30)
		self.model_dropdown.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
		self.model_dropdown.bind("<<ComboboxSelected>>", lambda e: self._schedule_preview())

		self.matting_var = tk.BooleanVar(value=True)
		self.matting_check = tk.Checkbutton(
			self.controls_panel,
			text="Enable Alpha Matting",
			variable=self.matting_var,
			font=(self.font_family, 10),
			bg=self.theme.bg_panel,
			fg=self.theme.fg_text,
			selectcolor=self.theme.bg_input,
			activebackground=self.theme.bg_panel,
			activeforeground=self.theme.fg_accent,
			command=self._schedule_preview
		)
		self.matting_check.grid(row=0, column=2, sticky=tk.W, padx=20, pady=5)

		fg_label = tk.Label(self.controls_panel, text="Foreground Threshold:", font=(self.font_family, 9),
							bg=self.theme.bg_panel, fg=self.theme.fg_grey)
		fg_label.grid(row=1, column=0, sticky=tk.W, pady=5)
		self.fg_slider = tk.Scale(self.controls_panel, from_=1, to=255, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
								  fg=self.theme.fg_text, troughcolor=self.theme.bg_input, highlightthickness=0,
								  command=self._on_fg_slide)
		self.fg_slider.set(240)
		self.fg_slider.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

		bg_label = tk.Label(self.controls_panel, text="Background Threshold:", font=(self.font_family, 9),
							bg=self.theme.bg_panel, fg=self.theme.fg_grey)
		bg_label.grid(row=2, column=0, sticky=tk.W, pady=5)
		self.bg_slider = tk.Scale(self.controls_panel, from_=1, to=255, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
								  fg=self.theme.fg_text, troughcolor=self.theme.bg_input, highlightthickness=0,
								  command=self._on_bg_slide)
		self.bg_slider.set(10)
		self.bg_slider.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

		erode_label = tk.Label(self.controls_panel, text="Matting Erode Size:", font=(self.font_family, 9),
							   bg=self.theme.bg_panel, fg=self.theme.fg_grey)
		erode_label.grid(row=3, column=0, sticky=tk.W, pady=5)
		self.erode_slider = tk.Scale(self.controls_panel, from_=0, to=40, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
									 fg=self.theme.fg_text, troughcolor=self.theme.bg_input, highlightthickness=0,
									 command=self._schedule_preview)
		self.erode_slider.set(10)
		self.erode_slider.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

		choke_label = tk.Label(self.controls_panel, text="Mask Choke (Pixels):", font=(self.font_family, 9),
							   bg=self.theme.bg_panel, fg=self.theme.fg_grey)
		choke_label.grid(row=4, column=0, sticky=tk.W, pady=5)
		self.choke_slider = tk.Scale(self.controls_panel, from_=0, to=15, orient=tk.HORIZONTAL, bg=self.theme.bg_panel,
									 fg=self.theme.fg_text, troughcolor=self.theme.bg_input, highlightthickness=0,
									 command=self._schedule_preview)
		self.choke_slider.set(0)
		self.choke_slider.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

		self.info_label = tk.Label(self.controls_panel, text="Waiting for UI...", font=(self.font_family, 10),
								   bg=self.theme.bg_panel,
								   fg=self.theme.fg_green)
		self.info_label.grid(row=1, column=2, rowspan=2, padx=20, sticky=tk.W)

		self.action_btn = tk.Button(
			self.controls_panel,
			text="PROCESS & SAVE",
			font=(self.font_family, 10, "bold"),
			bg=self.theme.bg_button,
			fg=self.theme.fg_text,
			activebackground=self.theme.bg_input,
			activeforeground=self.theme.fg_accent,
			bd=0,
			padx=20,
			pady=8,
			command=self._save_output,
			cursor="hand2"
		)
		self.action_btn.grid(row=3, column=2, rowspan=2, padx=20, sticky=tk.EW)

		self.grip = tk.Frame(self.root, bg=self.theme.bg_separator, cursor="size_nw_se")
		self.grip.place(relx=1.0, rely=1.0, anchor="se", width=15, height=15)

	def _bind_events(self) -> None:
		self.title_bar.bind("<Button-1>", self._start_drag)
		self.title_bar.bind("<B1-Motion>", self._execute_drag)

		self.grip.bind("<ButtonPress-1>", self._start_resize)
		self.grip.bind("<B1-Motion>", self._execute_resize)

		self.preview_canvas.bind("<MouseWheel>", self._on_mousewheel)
		self.preview_canvas.bind("<Button-4>", self._on_mousewheel)
		self.preview_canvas.bind("<Button-5>", self._on_mousewheel)

		self.preview_canvas.bind("<ButtonPress-1>", self._start_pan)
		self.preview_canvas.bind("<B1-Motion>", self._execute_pan)

		self.preview_canvas.bind("<Configure>", lambda e: self._render_image())

	def _start_drag(self, event: tk.Event) -> None:
		self._drag_data["x"] = event.x
		self._drag_data["y"] = event.y

	def _execute_drag(self, event: tk.Event) -> None:
		deltax = event.x - self._drag_data["x"]
		deltay = event.y - self._drag_data["y"]
		x = self.root.winfo_x() + deltax
		y = self.root.winfo_y() + deltay
		self.root.geometry(f"+{x}+{y}")

	def _start_resize(self, event: tk.Event) -> None:
		self._resize_data["x"] = event.x_root
		self._resize_data["y"] = event.y_root
		self._resize_data["width"] = self.root.winfo_width()
		self._resize_data["height"] = self.root.winfo_height()

	def _execute_resize(self, event: tk.Event) -> None:
		deltax = event.x_root - self._resize_data["x"]
		deltay = event.y_root - self._resize_data["y"]
		new_w = max(600, self._resize_data["width"] + deltax)
		new_h = max(400, self._resize_data["height"] + deltay)
		self.root.geometry(f"{new_w}x{new_h}")

	def _on_mousewheel(self, event: tk.Event) -> None:
		if event.num == 4 or getattr(event, 'delta', 0) > 0:
			self.zoom_level *= 1.1
		elif event.num == 5 or getattr(event, 'delta', 0) < 0:
			self.zoom_level *= 0.9

		self.zoom_level = max(0.1, min(self.zoom_level, 10.0))
		self._render_image()

	def _start_pan(self, event: tk.Event) -> None:
		self._pan_data["x"] = event.x
		self._pan_data["y"] = event.y

	def _execute_pan(self, event: tk.Event) -> None:
		dx = event.x - self._pan_data["x"]
		dy = event.y - self._pan_data["y"]
		self.pan_x += dx
		self.pan_y += dy
		self._pan_data["x"] = event.x
		self._pan_data["y"] = event.y
		self._render_image()

	def _load_current_image(self) -> None:
		if self.current_index >= len(self.input_paths):
			self.root.destroy()
			return

		self.zoom_level = 1.0
		self.pan_x = 0
		self.pan_y = 0
		self._last_rendered_size = (0, 0)

		self.raw_image = Image.open(self.input_paths[self.current_index]).convert("RGBA")

		self.preview_image = self.raw_image.copy()
		self.preview_image.thumbnail((800, 800), Image.Resampling.LANCZOS)

		self._schedule_preview()

	def _on_fg_slide(self, val) -> None:
		if int(val) <= self.bg_slider.get():
			self.fg_slider.set(self.bg_slider.get() + 1)
			return
		self._schedule_preview()

	def _on_bg_slide(self, val) -> None:
		if int(val) >= self.fg_slider.get():
			self.bg_slider.set(self.fg_slider.get() - 1)
			return
		self._schedule_preview()

	def _schedule_preview(self, *args) -> None:
		if not hasattr(self, 'preview_image'):
			return

		if self._preview_timer is not None:
			self.root.after_cancel(self._preview_timer)

		self._preview_timer = self.root.after(300, self._start_processing_thread)

	def _start_processing_thread(self) -> None:
		if self._is_processing:
			if self._preview_timer is not None:
				self.root.after_cancel(self._preview_timer)
			self._preview_timer = self.root.after(300, self._start_processing_thread)
			return

		self._is_processing = True
		self.info_label.config(text="Processing AI... please wait.", fg=self.theme.fg_accent)

		model_name = self.model_var.get()
		matting_enabled = self.matting_var.get()
		fg_val = int(self.fg_slider.get())
		bg_val = int(self.bg_slider.get())
		erode_val = int(self.erode_slider.get())
		choke_val = int(self.choke_slider.get())

		threading.Thread(
			target=self._process_image_task,
			args=(model_name, matting_enabled, fg_val, bg_val, erode_val, choke_val),
			daemon=True
		).start()

	def _process_image_task(self, model_name, matting_enabled, fg_val, bg_val, erode_val, choke_val) -> None:
		selected_session = self._get_session(model_name)

		if matting_enabled:
			processed = remove(
				self.preview_image,
				session=selected_session,
				post_process_mask=True,
				alpha_matting=True,
				alpha_matting_foreground_threshold=fg_val,
				alpha_matting_background_threshold=bg_val,
				alpha_matting_erode_size=erode_val
			)
		else:
			processed = remove(
				self.preview_image,
				session=selected_session,
				post_process_mask=True,
				alpha_matting=False
			)

		if choke_val > 0:
			r, g, b, a = processed.split()
			filter_size = (choke_val * 2) + 1
			a = a.filter(ImageFilter.MinFilter(filter_size))
			processed = Image.merge("RGBA", (r, g, b, a))

		self.root.after(0, self._apply_processed_image, processed)

	def _apply_processed_image(self, processed_image) -> None:
		self.current_processed_pil = processed_image
		self._last_rendered_size = (0, 0)
		total_files = len(self.input_paths)
		self.info_label.config(
			text=f"Image {self.current_index + 1} of {total_files}\n{self.input_paths[self.current_index].name}",
			fg=self.theme.fg_green
		)
		self._render_image()
		self._is_processing = False

	def _render_image(self) -> None:
		if not hasattr(self, 'current_processed_pil'):
			return

		canvas_w = self.preview_canvas.winfo_width()
		canvas_h = self.preview_canvas.winfo_height()

		if canvas_w < 10 or canvas_h < 10:
			canvas_w, canvas_h = 600, 400

		new_w = int(self.current_processed_pil.width * self.zoom_level)
		new_h = int(self.current_processed_pil.height * self.zoom_level)

		if self._last_rendered_size != (new_w, new_h):
			resized_image = self.current_processed_pil.resize((max(1, new_w), max(1, new_h)), Image.Resampling.LANCZOS)
			self.tk_img = ImageTk.PhotoImage(resized_image)
			self._last_rendered_size = (new_w, new_h)

		self.preview_canvas.delete("all")
		self.preview_canvas.create_image(
			(canvas_w // 2) + self.pan_x,
			(canvas_h // 2) + self.pan_y,
			image=self.tk_img,
			anchor=tk.CENTER
		)

	def _save_output(self) -> None:
		self.info_label.config(text="Saving full resolution... please wait.", fg=self.theme.fg_accent)
		self.root.update_idletasks()

		input_path = self.input_paths[self.current_index]
		source_dir_path = input_path.parent

		if len(self.input_paths) > 1:
			output_dir = source_dir_path / 'No_BG'
			output_dir.mkdir(parents=True, exist_ok=True)
			output_path = output_dir / f'{input_path.stem}_NoBG.png'
		else:
			output_path = source_dir_path / f"{input_path.stem}_NoBG.png"

		selected_session = self._get_session(self.model_var.get())
		matting_enabled = self.matting_var.get()
		choke_val = int(self.choke_slider.get())

		if matting_enabled:
			final_output = remove(
				self.raw_image,
				session=selected_session,
				post_process_mask=True,
				alpha_matting=True,
				alpha_matting_foreground_threshold=int(self.fg_slider.get()),
				alpha_matting_background_threshold=int(self.bg_slider.get()),
				alpha_matting_erode_size=int(self.erode_slider.get())
			)
		else:
			final_output = remove(
				self.raw_image,
				session=selected_session,
				post_process_mask=True,
				alpha_matting=False
			)

		if choke_val > 0:
			r, g, b, a = final_output.split()
			filter_size = (choke_val * 2) + 1
			a = a.filter(ImageFilter.MinFilter(filter_size))
			final_output = Image.merge("RGBA", (r, g, b, a))

		final_output.save(output_path, "PNG")

		self.current_index += 1
		self._load_current_image()

	def run(self) -> None:
		self.root.mainloop()


if __name__ == "__main__":
	app = BackgroundRemoverUI()
	app.run()