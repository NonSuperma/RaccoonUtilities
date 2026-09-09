from pathlib import Path
import os
import sys
import subprocess
import ctypes
import tempfile
import tkinter as tk
from playsound3 import playsound
from Raccoon.windowsUtilities import win_file_path, count_open_windows, ask_exit
from Raccoon.miscUtilities import seconds_to_hhmmss, get_bundled_file_path
from Raccoon.errors import MissingInputError

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

if os.name == 'nt':
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    os.add_dll_directory(base_dir)
    os.environ["PATH"] = base_dir + os.pathsep + os.environ.get("PATH", "")

FFMPEG_PATH = get_bundled_file_path('ffmpeg.exe')
CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def show_console():
    if os.name == 'nt':
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)
        else:
            ctypes.windll.kernel32.AllocConsole()
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stdin = open("CONIN$", "r")


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while (candidate := parent / f"{stem} ({counter}){suffix}").exists():
        counter += 1
    return candidate


def run_ffmpeg_with_progress(cmd: list[str], duration: float) -> bool:
    show_console()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        creationflags=CREATION_FLAGS
    )

    stats = {}
    bar_width = 25

    while True:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue

        line = line.strip()
        if "=" in line:
            key, val = line.split("=", 1)
            stats[key.strip()] = val.strip()

        if line.startswith("progress="):
            out_time_us = stats.get("out_time_us", "0")
            if out_time_us.isdigit() and duration > 0:
                current_sec = int(out_time_us) / 1_000_000
                pct = min(100.0, max(0.0, (current_sec / duration) * 100.0))
            else:
                current_sec = duration if stats.get("progress") == "end" else 0.0
                pct = 100.0 if stats.get("progress") == "end" else 0.0

            filled = int(bar_width * (pct / 100.0))
            bar = "█" * filled + "░" * (bar_width - filled)
            fps = stats.get("fps", "0")
            speed = stats.get("speed", "N/A")
            cur_time_str = seconds_to_hhmmss(current_sec)
            total_time_str = seconds_to_hhmmss(duration)

            sys.stdout.write(f"\rEncoding: [{bar}] {pct:5.1f}% | {cur_time_str} / {total_time_str} | FPS: {fps} | Speed: {speed}")
            sys.stdout.flush()

    proc.wait()
    sys.stdout.write("\n")
    sys.stdout.flush()
    return proc.returncode == 0


def open_crop_gui(input_path: str, timestamp: float, rotation: int, current_crop: tuple[int, int, int, int] | None) -> tuple[int, int, int, int] | None | str:
    temp_frame = os.path.join(tempfile.gettempdir(), f"crop_frame_orig_{os.getpid()}.png")
    temp_disp_frame = os.path.join(tempfile.gettempdir(), f"crop_frame_disp_{os.getpid()}.png")

    cmd = [
        FFMPEG_PATH, '-y', '-nostdin', '-v', 'error',
        '-ss', str(timestamp),
        '-i', str(input_path)
    ]
    v_filters = []
    if rotation == 90:
        v_filters.append("transpose=1")
    elif rotation == 180:
        v_filters.append("transpose=1,transpose=1")
    elif rotation == 270:
        v_filters.append("transpose=2")

    if v_filters:
        cmd.extend(['-filter:v', ",".join(v_filters)])

    cmd.extend(['-frames:v', '1', '-c:v', 'png', temp_frame])
    result = subprocess.run(cmd, creationflags=CREATION_FLAGS)
    if result.returncode != 0 or not os.path.exists(temp_frame):
        return current_crop

    root = tk.Tk()
    root.title("Crop Video")
    root.configure(bg="#202020")
    root.attributes('-topmost', True)
    root.resizable(False, False)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    canvas_max_w = max(400, screen_w - 140)
    canvas_max_h = max(300, screen_h - 220)

    if HAS_PIL:
        orig_image = Image.open(temp_frame)
        orig_w, orig_h = orig_image.size
    else:
        raw_photo = tk.PhotoImage(file=temp_frame)
        orig_w = raw_photo.width()
        orig_h = raw_photo.height()
        del raw_photo

    scale = min(canvas_max_w / orig_w, canvas_max_h / orig_h)
    disp_w = max(2, int(orig_w * scale))
    disp_h = max(2, int(orig_h * scale))

    if HAS_PIL:
        resized_image = orig_image.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_image)
    else:
        scale_filter = list(v_filters)
        scale_filter.append(f"scale={disp_w}:{disp_h}")
        cmd_scale = [
            FFMPEG_PATH, '-y', '-nostdin', '-v', 'error',
            '-ss', str(timestamp),
            '-i', str(input_path),
            '-filter:v', ",".join(scale_filter),
            '-frames:v', '1', '-c:v', 'png', temp_disp_frame
        ]
        subprocess.run(cmd_scale, creationflags=CREATION_FLAGS)
        if os.path.exists(temp_disp_frame):
            tk_img = tk.PhotoImage(file=temp_disp_frame)
        else:
            tk_img = tk.PhotoImage(file=temp_frame)

    pad_x = 20
    pad_y = 20
    canvas_w = disp_w + (pad_x * 2)
    canvas_h = disp_h + (pad_y * 2)

    img_x1 = pad_x
    img_y1 = pad_y
    img_x2 = pad_x + disp_w
    img_y2 = pad_y + disp_h

    if current_crop:
        cx, cy, cw, ch = current_crop
        crop_x1 = img_x1 + int(cx * scale)
        crop_y1 = img_y1 + int(cy * scale)
        crop_x2 = crop_x1 + int(cw * scale)
        crop_y2 = crop_y1 + int(ch * scale)
    else:
        crop_x1 = img_x1
        crop_y1 = img_y1
        crop_x2 = img_x2
        crop_y2 = img_y2

    final_crop = current_crop
    active_ratio: float | None = None
    drag_mode: str | None = None
    start_mouse_x = 0
    start_mouse_y = 0
    initial_crop = (crop_x1, crop_y1, crop_x2, crop_y2)

    top_bar = tk.Frame(root, bg="#202020", pady=10)
    top_bar.pack(fill="x")

    ratio_frame = tk.Frame(top_bar, bg="#202020")
    ratio_frame.pack(side="left", padx=15)

    ratio_buttons = {}
    ratios = [
        ("Free", None),
        ("Original", orig_w / orig_h),
        ("16:9", 16.0 / 9.0),
        ("4:3", 4.0 / 3.0),
        ("1:1", 1.0),
        ("9:16", 9.0 / 16.0),
        ("3:2", 3.0 / 2.0),
    ]

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="#181818", highlightthickness=0)
    canvas.pack(padx=10, pady=5)
    canvas.create_image(img_x1, img_y1, anchor="nw", image=tk_img)

    bottom_bar = tk.Frame(root, bg="#202020", pady=10)
    bottom_bar.pack(fill="x")

    res_label = tk.Label(bottom_bar, text="", fg="#aaaaaa", bg="#202020", font=("Segoe UI", 9))
    res_label.pack(side="left", padx=15)

    def draw_crop_overlay():
        nonlocal crop_x1, crop_y1, crop_x2, crop_y2
        canvas.delete("overlay")

        canvas.create_rectangle(img_x1, img_y1, img_x2, crop_y1, fill="#000000", stipple="gray50", outline="", tags="overlay")
        canvas.create_rectangle(img_x1, crop_y2, img_x2, img_y2, fill="#000000", stipple="gray50", outline="", tags="overlay")
        canvas.create_rectangle(img_x1, crop_y1, crop_x1, crop_y2, fill="#000000", stipple="gray50", outline="", tags="overlay")
        canvas.create_rectangle(crop_x2, crop_y1, img_x2, crop_y2, fill="#000000", stipple="gray50", outline="", tags="overlay")

        canvas.create_rectangle(crop_x1, crop_y1, crop_x2, crop_y2, outline="#ffffff", width=2, tags="overlay")

        cw = crop_x2 - crop_x1
        ch = crop_y2 - crop_y1

        if cw > 30 and ch > 30:
            x_t1 = crop_x1 + cw / 3
            x_t2 = crop_x1 + 2 * cw / 3
            y_t1 = crop_y1 + ch / 3
            y_t2 = crop_y1 + 2 * ch / 3
            canvas.create_line(x_t1, crop_y1, x_t1, crop_y2, fill="#888888", dash=(2, 2), tags="overlay")
            canvas.create_line(x_t2, crop_y1, x_t2, crop_y2, fill="#888888", dash=(2, 2), tags="overlay")
            canvas.create_line(crop_x1, y_t1, crop_x2, y_t1, fill="#888888", dash=(2, 2), tags="overlay")
            canvas.create_line(crop_x1, y_t2, crop_x2, y_t2, fill="#888888", dash=(2, 2), tags="overlay")

        handle_len = min(16, cw // 3, ch // 3)
        lw = 3

        canvas.create_line(crop_x1, crop_y1 + handle_len, crop_x1, crop_y1, crop_x1 + handle_len, crop_y1, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(crop_x2 - handle_len, crop_y1, crop_x2, crop_y1, crop_x2, crop_y1 + handle_len, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(crop_x1, crop_y2 - handle_len, crop_x1, crop_y2, crop_x1 + handle_len, crop_y2, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(crop_x2 - handle_len, crop_y2, crop_x2, crop_y2, crop_x2, crop_y2 - handle_len, fill="#ffffff", width=lw, tags="overlay")

        mid_x = (crop_x1 + crop_x2) / 2
        mid_y = (crop_y1 + crop_y2) / 2
        bar_len = min(12, handle_len)
        canvas.create_line(mid_x - bar_len, crop_y1, mid_x + bar_len, crop_y1, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(mid_x - bar_len, crop_y2, mid_x + bar_len, crop_y2, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(crop_x1, mid_y - bar_len, crop_x1, mid_y + bar_len, fill="#ffffff", width=lw, tags="overlay")
        canvas.create_line(crop_x2, mid_y - bar_len, crop_x2, mid_y + bar_len, fill="#ffffff", width=lw, tags="overlay")

        real_w = int(round(cw / scale))
        real_h = int(round(ch / scale))
        real_w -= real_w % 2
        real_h -= real_h % 2
        res_label.config(text=f"Selected: {real_w} × {real_h} px")

    def apply_aspect_ratio(ratio: float | None):
        nonlocal crop_x1, crop_y1, crop_x2, crop_y2, active_ratio
        active_ratio = ratio
        for name, btn in ratio_buttons.items():
            if (name == "Free" and ratio is None) or (name != "Free" and ratio is not None and ratios[list(ratio_buttons.keys()).index(name)][1] == ratio):
                btn.configure(bg="#0078d4", fg="#ffffff")
            else:
                btn.configure(bg="#2d2d2d", fg="#cccccc")

        if ratio is not None:
            center_x = (crop_x1 + crop_x2) / 2
            center_y = (crop_y1 + crop_y2) / 2
            cur_w = crop_x2 - crop_x1
            cur_h = crop_y2 - crop_y1

            if cur_w / cur_h > ratio:
                new_h = cur_h
                new_w = new_h * ratio
            else:
                new_w = cur_w
                new_h = new_w / ratio

            if new_w > disp_w:
                new_w = disp_w
                new_h = new_w / ratio
            if new_h > disp_h:
                new_h = disp_h
                new_w = new_h * ratio

            crop_x1 = max(img_x1, min(img_x2 - new_w, center_x - new_w / 2))
            crop_y1 = max(img_y1, min(img_y2 - new_h, center_y - new_h / 2))
            crop_x2 = crop_x1 + new_w
            crop_y2 = crop_y1 + new_h

        draw_crop_overlay()

    for name, r_val in ratios:
        btn = tk.Button(
            ratio_frame,
            text=name,
            bg="#2d2d2d",
            fg="#cccccc",
            activebackground="#0078d4",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=3,
            font=("Segoe UI", 9),
            command=lambda r=r_val: apply_aspect_ratio(r)
        )
        btn.pack(side="left", padx=2)
        ratio_buttons[name] = btn

    def get_hit_mode(x, y) -> str | None:
        r = 12
        if abs(x - crop_x1) <= r and abs(y - crop_y1) <= r:
            return "nw"
        if abs(x - crop_x2) <= r and abs(y - crop_y1) <= r:
            return "ne"
        if abs(x - crop_x1) <= r and abs(y - crop_y2) <= r:
            return "sw"
        if abs(x - crop_x2) <= r and abs(y - crop_y2) <= r:
            return "se"
        if abs(y - crop_y1) <= r and crop_x1 <= x <= crop_x2:
            return "n"
        if abs(y - crop_y2) <= r and crop_x1 <= x <= crop_x2:
            return "s"
        if abs(x - crop_x1) <= r and crop_y1 <= y <= crop_y2:
            return "w"
        if abs(x - crop_x2) <= r and crop_y1 <= y <= crop_y2:
            return "e"
        if crop_x1 < x < crop_x2 and crop_y1 < y < crop_y2:
            return "move"
        return None

    def on_mouse_motion(event):
        if drag_mode is not None:
            return
        mode = get_hit_mode(event.x, event.y)
        cursor_map = {
            "nw": "size_nw_se",
            "se": "size_nw_se",
            "ne": "size_ne_sw",
            "sw": "size_ne_sw",
            "n": "size_ns",
            "s": "size_ns",
            "w": "size_we",
            "e": "size_we",
            "move": "fleur",
            None: "arrow"
        }
        canvas.config(cursor=cursor_map.get(mode, "arrow"))

    def on_mouse_press(event):
        nonlocal drag_mode, start_mouse_x, start_mouse_y, initial_crop
        drag_mode = get_hit_mode(event.x, event.y)
        start_mouse_x = event.x
        start_mouse_y = event.y
        initial_crop = (crop_x1, crop_y1, crop_x2, crop_y2)

    def on_mouse_drag(event):
        nonlocal crop_x1, crop_y1, crop_x2, crop_y2
        if not drag_mode:
            return

        dx = event.x - start_mouse_x
        dy = event.y - start_mouse_y
        ix1, iy1, ix2, iy2 = initial_crop
        min_size = 24

        if drag_mode == "move":
            box_w = ix2 - ix1
            box_h = iy2 - iy1
            new_x1 = max(img_x1, min(img_x2 - box_w, ix1 + dx))
            new_y1 = max(img_y1, min(img_y2 - box_h, iy1 + dy))
            crop_x1 = new_x1
            crop_y1 = new_y1
            crop_x2 = new_x1 + box_w
            crop_y2 = new_y1 + box_h
        elif active_ratio is None:
            if "w" in drag_mode:
                crop_x1 = max(img_x1, min(ix2 - min_size, ix1 + dx))
            if "e" in drag_mode:
                crop_x2 = min(img_x2, max(ix1 + min_size, ix2 + dx))
            if "n" in drag_mode:
                crop_y1 = max(img_y1, min(iy2 - min_size, iy1 + dy))
            if "s" in drag_mode:
                crop_y2 = min(img_y2, max(iy1 + min_size, iy2 + dy))
        else:
            r = active_ratio
            if drag_mode == "se":
                nw = max(min_size, ix2 - ix1 + dx)
                nh = nw / r
                if ix1 + nw > img_x2:
                    nw = img_x2 - ix1
                    nh = nw / r
                if iy1 + nh > img_y2:
                    nh = img_y2 - iy1
                    nw = nh * r
                crop_x2 = ix1 + max(min_size, nw)
                crop_y2 = iy1 + max(min_size / r, nh)
            elif drag_mode == "nw":
                nw = max(min_size, ix2 - ix1 - dx)
                nh = nw / r
                if ix2 - nw < img_x1:
                    nw = ix2 - img_x1
                    nh = nw / r
                if iy2 - nh < img_y1:
                    nh = iy2 - img_y1
                    nw = nh * r
                crop_x1 = ix2 - max(min_size, nw)
                crop_y1 = iy2 - max(min_size / r, nh)
            elif drag_mode == "ne":
                nw = max(min_size, ix2 - ix1 + dx)
                nh = nw / r
                if ix1 + nw > img_x2:
                    nw = img_x2 - ix1
                    nh = nw / r
                if iy2 - nh < img_y1:
                    nh = iy2 - img_y1
                    nw = nh * r
                crop_x2 = ix1 + max(min_size, nw)
                crop_y1 = iy2 - max(min_size / r, nh)
            elif drag_mode == "sw":
                nw = max(min_size, ix2 - ix1 - dx)
                nh = nw / r
                if ix2 - nw < img_x1:
                    nw = ix2 - img_x1
                    nh = nw / r
                if iy1 + nh > img_y2:
                    nh = img_y2 - iy1
                    nw = nh * r
                crop_x1 = ix2 - max(min_size, nw)
                crop_y2 = iy1 + max(min_size / r, nh)
            elif drag_mode in ("e", "w"):
                nw = max(min_size, (ix2 - ix1 + dx) if drag_mode == "e" else (ix2 - ix1 - dx))
                nh = nw / r
                cy = (iy1 + iy2) / 2
                if cy - nh / 2 < img_y1 or cy + nh / 2 > img_y2:
                    nh = min(cy - img_y1, img_y2 - cy) * 2
                    nw = nh * r
                if drag_mode == "e":
                    crop_x2 = min(img_x2, ix1 + nw)
                else:
                    crop_x1 = max(img_x1, ix2 - nw)
                crop_y1 = cy - nh / 2
                crop_y2 = cy + nh / 2
            elif drag_mode in ("n", "s"):
                nh = max(min_size / r, (iy2 - iy1 + dy) if drag_mode == "s" else (iy2 - iy1 - dy))
                nw = nh * r
                cx = (ix1 + ix2) / 2
                if cx - nw / 2 < img_y1 or cx + nw / 2 > img_y2:
                    nw = min(cx - img_x1, img_x2 - cx) * 2
                    nh = nw / r
                if drag_mode == "s":
                    crop_y2 = min(img_y2, iy1 + nh)
                else:
                    crop_y1 = max(img_y1, iy2 - nh)
                crop_x1 = cx - nw / 2
                crop_x2 = cx + nw / 2

        draw_crop_overlay()

    def on_mouse_release(event):
        nonlocal drag_mode
        drag_mode = None

    canvas.bind("<Motion>", on_mouse_motion)
    canvas.bind("<ButtonPress-1>", on_mouse_press)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_release)

    def on_reset():
        nonlocal crop_x1, crop_y1, crop_x2, crop_y2, active_ratio
        crop_x1 = img_x1
        crop_y1 = img_y1
        crop_x2 = img_x2
        crop_y2 = img_y2
        apply_aspect_ratio(None)

    def on_clear():
        nonlocal final_crop
        final_crop = "CLEAR"
        root.destroy()

    def on_apply():
        nonlocal final_crop
        cw = crop_x2 - crop_x1
        ch = crop_y2 - crop_y1
        rx = crop_x1 - img_x1
        ry = crop_y1 - img_y1

        vx = int(round(rx / scale))
        vy = int(round(ry / scale))
        vw = int(round(cw / scale))
        vh = int(round(ch / scale))

        vw -= vw % 2
        vh -= vh % 2
        vx -= vx % 2
        vy -= vy % 2

        vx = max(0, min(vx, orig_w - vw))
        vy = max(0, min(vy, orig_h - vh))

        if vw >= orig_w and vh >= orig_h and vx == 0 and vy == 0:
            final_crop = "CLEAR"
        else:
            final_crop = (vx, vy, vw, vh)
        root.destroy()

    def on_cancel():
        root.destroy()

    actions_frame = tk.Frame(bottom_bar, bg="#202020")
    actions_frame.pack(side="right", padx=15)

    btn_reset = tk.Button(actions_frame, text="Reset", bg="#2d2d2d", fg="#cccccc", relief="flat", padx=12, pady=4, font=("Segoe UI", 9), command=on_reset)
    btn_reset.pack(side="left", padx=4)

    btn_clear = tk.Button(actions_frame, text="Turn Off Crop", bg="#2d2d2d", fg="#cccccc", relief="flat", padx=12, pady=4, font=("Segoe UI", 9), command=on_clear)
    btn_clear.pack(side="left", padx=4)

    btn_cancel = tk.Button(actions_frame, text="Cancel", bg="#2d2d2d", fg="#cccccc", relief="flat", padx=12, pady=4, font=("Segoe UI", 9), command=on_cancel)
    btn_cancel.pack(side="left", padx=4)

    btn_apply = tk.Button(actions_frame, text="Apply", bg="#0078d4", fg="#ffffff", relief="flat", padx=16, pady=4, font=("Segoe UI", 9, "bold"), command=on_apply)
    btn_apply.pack(side="left", padx=4)

    root.bind("<Return>", lambda e: on_apply())
    root.bind("<Escape>", lambda e: on_cancel())

    root.update_idletasks()
    win_w = canvas_w + 20
    win_h = canvas_h + 120
    pos_x = max(0, (screen_w - win_w) // 2)
    pos_y = max(0, (screen_h - win_h) // 2)
    root.geometry(f"+{pos_x}+{pos_y}")

    apply_aspect_ratio(None)
    root.mainloop()

    for p in (temp_frame, temp_disp_frame):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

    return final_crop


def preview_and_cut(input_path, output_path):
    import mpv
    input_path = str(input_path)
    output_path = str(get_unique_path(Path(output_path)))

    player = mpv.MPV(
        input_default_bindings=True,
        input_vo_keyboard=True,
        osc=True,
        border=False,
        osd_font_size=26,
        keep_open=True,
        loop_file='inf',
        volume=60,
        volume_max=150,
        hwdec='auto-safe',
        vo='gpu',
        gpu_context='d3d11',
        hr_seek='yes',
        hr_seek_framedrop='yes',
        hidpi_window_scale=True,
        cache='yes',
        demuxer_max_bytes='512MiB',
        demuxer_max_back_bytes='256MiB',
        demuxer_readahead_secs=30
    )

    start_time = 0.0
    end_time: float | None = None
    start_marked = False
    video_duration = None
    cut_authorized = False
    active_menu = None
    export_mode = 'copy'
    include_audio = True
    strip_metadata = False
    speed_factor = 1.0
    current_rotation = 0
    crop_rect: tuple[int, int, int, int] | None = None

    webp_fps = 15
    webp_scale = 'original'
    webp_quality = 70
    webp_compression = 6

    def update_overlay():
        if active_menu == 'encode':
            lines = [
                "=== SELECT ENCODE PRESET ===",
                "[1] Ultrafast  (Larger size, CRF 22)",
                "[2] Balanced   (CRF 20)",
                "[3] Slow / HQ  (Minimal loss, CRF 16)",
                "[Esc] Cancel Menu"
            ]
        elif active_menu == 'options':
            audio_checkbox = "[*]" if include_audio else "[ ]"
            metadata_checkbox = "[*]" if strip_metadata else "[ ]"
            speed_display = f"{int(speed_factor * 100)}%" if speed_factor.is_integer() else f"{speed_factor * 100:.0f}%"
            crop_display = f"[{crop_rect[2]}x{crop_rect[3]}]" if crop_rect else "[Off]"
            lines = [
                "=== OPTIONS MENU ===",
                f"[1] Audio: {audio_checkbox}",
                f"[2] Strip Metadata: {metadata_checkbox}",
                f"[3] Speed: {speed_display} >",
                f"[4] Crop: {crop_display} >",
                "[5] WebP Settings >",
                "[Esc] Close Options"
            ]
        elif active_menu == 'speed':
            lines = [
                "=== SPEED SELECT ===",
                "[1] 25%",
                "[2] 50%",
                "[3] 75%",
                "[4] 100% (Normal)",
                "[5] 125%",
                "[6] 150%",
                "[Esc] Back to Options"
            ]
        elif active_menu == 'webp':
            fps_disp = f"{webp_fps} fps" if webp_fps != 'original' else "Original"
            scale_disp = "Original" if webp_scale == 'original' else (f"{webp_scale}px" if webp_scale == '800' else f"{webp_scale}p")
            lines = [
                "=== WEBP MENU ===",
                f"[1] FPS: {fps_disp} >",
                f"[2] Scale: {scale_disp} >",
                f"[3] Quality (q:v): {webp_quality} >",
                f"[4] Compression: {webp_compression} >",
                "[5] Export WebP Now",
                "[Esc] Close WebP Menu"
            ]
        elif active_menu == 'webp_fps':
            lines = [
                "=== WEBP FPS ===",
                "[1] 10 fps",
                "[2] 15 fps",
                "[3] 20 fps",
                "[4] 24 fps",
                "[5] 30 fps",
                "[6] Original FPS",
                "[Esc] Back to WebP Menu"
            ]
        elif active_menu == 'webp_scale':
            lines = [
                "=== WEBP SCALE ===",
                "[1] Original Resolution",
                "[2] Width 800px",
                "[3] 1080p",
                "[4] 720p",
                "[5] 480p",
                "[6] 360p",
                "[Esc] Back to WebP Menu"
            ]
        elif active_menu == 'webp_quality':
            lines = [
                "=== WEBP QUALITY (q:v) ===",
                "[1] 50",
                "[2] 60",
                "[3] 70",
                "[4] 80",
                "[5] 90",
                "[6] 100",
                "[Esc] Back to WebP Menu"
            ]
        elif active_menu == 'webp_compression':
            lines = [
                "=== COMPRESSION LEVEL ===",
                "[1] Level 1 (Fastest)",
                "[2] Level 2",
                "[3] Level 3",
                "[4] Level 4",
                "[5] Level 5",
                "[6] Level 6 (Best, Default)",
                "[Esc] Back to WebP Menu"
            ]
        else:
            lines = ["S (Start) | E (End) | Alt+S / Alt+E (Jump) |\nQ (Direct Copy) | Alt+Q (Re-encode) |\nW (WebP) | O (Options)"]
            if start_marked:
                lines.append(f'Start marked at: {seconds_to_hhmmss(start_time)}')
            if end_time is not None:
                lines.append(f'End marked at:   {seconds_to_hhmmss(end_time)}')
            if crop_rect is not None:
                lines.append(f'Crop: {crop_rect[2]}x{crop_rect[3]} @ ({crop_rect[0]},{crop_rect[1]})')
        player.osd_msg1 = "\n".join(lines)

    def trigger_cut(mode):
        nonlocal cut_authorized, export_mode
        if end_time is not None and start_time >= end_time:
            player.show_text('Warning: Start time must be before End time!', duration=3000)
            return
        export_mode = mode
        cut_authorized = True
        player.quit()

    @player.property_observer('duration')
    def on_duration(name, value):
        nonlocal video_duration
        if value is not None:
            video_duration = value

    @player.on_key_press('s')
    def set_start():
        if active_menu is not None: return
        nonlocal start_time, start_marked
        start_time = player.time_pos or 0.0
        start_marked = True
        update_overlay()

    @player.on_key_press('e')
    def set_end():
        if active_menu is not None: return
        nonlocal end_time
        end_time = player.time_pos or 0.0
        update_overlay()

    def jump_to_start():
        if active_menu is not None: return
        if start_marked:
            player.seek(start_time, 'absolute')
        else:
            player.show_text('Start time not set', duration=2000)

    def jump_to_end():
        if active_menu is not None: return
        if end_time is not None:
            player.seek(end_time, 'absolute')
        else:
            player.show_text('End time not set', duration=2000)

    @player.on_key_press('alt+s')
    def on_press_alt_s():
        jump_to_start()

    @player.on_key_press('Alt+s')
    def on_press_alt_s_title():
        jump_to_start()

    @player.on_key_press('Alt+S')
    def on_press_alt_s_upper():
        jump_to_start()

    @player.on_key_press('alt+e')
    def on_press_alt_e():
        jump_to_end()

    @player.on_key_press('Alt+e')
    def on_press_alt_e_title():
        jump_to_end()

    @player.on_key_press('Alt+E')
    def on_press_alt_e_upper():
        jump_to_end()

    @player.on_key_press('ctrl+e')
    def export_current_frame():
        if active_menu is not None: return
        timestamp = seconds_to_hhmmss(player.time_pos or 0.0).replace(':', '-')
        output_dir = Path(input_path).parent
        frame_path = get_unique_path(output_dir / f"{Path(input_path).stem}_frame_{timestamp}.png")
        cmd = [
            FFMPEG_PATH, '-n', '-nostdin', '-v', 'error',
            '-ss', str(player.time_pos or 0.0),
            '-i', input_path,
        ]
        v_filters = []
        if current_rotation == 90:
            v_filters.append("transpose=1")
        elif current_rotation == 180:
            v_filters.append("transpose=1,transpose=1")
        elif current_rotation == 270:
            v_filters.append("transpose=2")

        if crop_rect is not None:
            cx, cy, cw, ch = crop_rect
            v_filters.append(f"crop={cw}:{ch}:{cx}:{cy}")

        if v_filters:
            cmd.extend(['-filter:v', ",".join(v_filters)])

        if strip_metadata:
            cmd.extend(['-map_metadata', '-1'])

        cmd.extend(['-frames:v', '1', '-c:v', 'png', str(frame_path)])
        result = subprocess.run(cmd, creationflags=CREATION_FLAGS)
        if result.returncode == 0:
            player.show_text(f'Frame exported: {frame_path.name}', duration=2500)
        else:
            player.show_text('Frame export failed', duration=2500)

    @player.on_key_press('q')
    def direct_copy():
        if active_menu is None:
            trigger_cut('copy')

    @player.on_key_press('alt+q')
    def open_encode_menu():
        nonlocal active_menu
        active_menu = 'encode'
        update_overlay()

    def open_options_menu():
        nonlocal active_menu
        active_menu = 'options'
        update_overlay()

    def open_webp_menu():
        nonlocal active_menu
        active_menu = 'webp'
        update_overlay()

    @player.on_key_press('o')
    def on_press_o():
        open_options_menu()

    @player.on_key_press('O')
    def on_press_upper_o():
        open_options_menu()

    @player.on_key_press('w')
    def on_press_w():
        open_webp_menu()

    @player.on_key_press('W')
    def on_press_upper_w():
        open_webp_menu()

    @player.on_key_press('1')
    def select_one():
        nonlocal active_menu, include_audio, speed_factor, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'encode':
            trigger_cut('ultrafast')
        elif active_menu == 'options':
            include_audio = not include_audio
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.25
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'webp':
            active_menu = 'webp_fps'
            update_overlay()
        elif active_menu == 'webp_fps':
            webp_fps = 10
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = 'original'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 50
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 1
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('2')
    def select_two():
        nonlocal active_menu, strip_metadata, speed_factor, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'encode':
            trigger_cut('balanced')
        elif active_menu == 'options':
            strip_metadata = not strip_metadata
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.50
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'webp':
            active_menu = 'webp_scale'
            update_overlay()
        elif active_menu == 'webp_fps':
            webp_fps = 15
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = '800'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 60
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 2
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('3')
    def select_three():
        nonlocal active_menu, speed_factor, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'encode':
            trigger_cut('slow')
        elif active_menu == 'options':
            active_menu = 'speed'
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.75
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'webp':
            active_menu = 'webp_quality'
            update_overlay()
        elif active_menu == 'webp_fps':
            webp_fps = 20
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = '1080'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 70
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 3
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('4')
    def select_four():
        nonlocal active_menu, speed_factor, crop_rect, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'speed':
            speed_factor = 1.0
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'options':
            was_paused = player.pause
            player.pause = True
            chosen_crop = open_crop_gui(input_path, player.time_pos or 0.0, current_rotation, crop_rect)
            if chosen_crop == "CLEAR":
                crop_rect = None
            elif chosen_crop is not None:
                crop_rect = chosen_crop
            player.pause = was_paused
            update_overlay()
        elif active_menu == 'webp':
            active_menu = 'webp_compression'
            update_overlay()
        elif active_menu == 'webp_fps':
            webp_fps = 24
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = '720'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 80
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 4
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('5')
    def select_five():
        nonlocal active_menu, speed_factor, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'options':
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 1.25
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'webp':
            trigger_cut('webp')
        elif active_menu == 'webp_fps':
            webp_fps = 30
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = '480'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 90
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 5
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('6')
    def select_six():
        nonlocal active_menu, speed_factor, webp_fps, webp_scale, webp_quality, webp_compression
        if active_menu == 'speed':
            speed_factor = 1.50
            active_menu = 'options'
            update_overlay()
        elif active_menu == 'webp_fps':
            webp_fps = 'original'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_scale':
            webp_scale = '360'
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_quality':
            webp_quality = 100
            active_menu = 'webp'
            update_overlay()
        elif active_menu == 'webp_compression':
            webp_compression = 6
            active_menu = 'webp'
            update_overlay()

    @player.on_key_press('esc')
    def cancel_menu():
        nonlocal active_menu
        if active_menu in ('webp_fps', 'webp_scale', 'webp_quality', 'webp_compression'):
            active_menu = 'webp'
        elif active_menu == 'speed':
            active_menu = 'options'
        elif active_menu in ('encode', 'options', 'webp'):
            active_menu = None
        update_overlay()

    @player.on_key_press('Alt+r')
    def rotate_clockwise():
        nonlocal current_rotation, crop_rect
        current_rotation = (current_rotation + 90) % 360
        crop_rect = None
        player['video-rotate'] = current_rotation
        update_overlay()

    @player.on_key_press('Alt+R')
    def rotate_counter_clockwise():
        nonlocal current_rotation, crop_rect
        current_rotation = (current_rotation - 90) % 360
        crop_rect = None
        player['video-rotate'] = current_rotation
        update_overlay()

    update_overlay()
    player.play(input_path)
    player.wait_for_playback()
    player.terminate()
    del player

    if not cut_authorized:
        return False, output_path

    if end_time is None:
        if video_duration is None:
            return False, output_path
        end_time = video_duration

    duration = end_time - start_time
    output_duration = duration / speed_factor

    presets = {
        'ultrafast': {'v': ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '22'], 'a': ['-c:a', 'aac', '-b:a', '192k']},
        'balanced': {'v': ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20'], 'a': ['-c:a', 'aac', '-b:a', '192k']},
        'slow': {'v': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '16'], 'a': ['-c:a', 'aac', '-b:a', '256k']},
    }

    if export_mode == 'webp':
        output_path = str(get_unique_path(Path(output_path).with_suffix('.webp')))
        cmd = [
            FFMPEG_PATH, '-y', '-nostdin',
            '-v', 'error',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', input_path,
        ]
        v_filters = []
        if current_rotation == 90:
            v_filters.append("transpose=1")
        elif current_rotation == 180:
            v_filters.append("transpose=1,transpose=1")
        elif current_rotation == 270:
            v_filters.append("transpose=2")

        if crop_rect is not None:
            cx, cy, cw, ch = crop_rect
            v_filters.append(f"crop={cw}:{ch}:{cx}:{cy}")

        if speed_factor != 1.0:
            v_filters.append(f"setpts={1.0 / speed_factor}*(PTS-STARTPTS)")

        if webp_fps != 'original':
            v_filters.append(f"fps={webp_fps}")

        if webp_scale == '800':
            v_filters.append("scale=800:-1:flags=lanczos")
        elif webp_scale == '1080':
            v_filters.append("scale=-1:1080:flags=lanczos")
        elif webp_scale == '720':
            v_filters.append("scale=-1:720:flags=lanczos")
        elif webp_scale == '480':
            v_filters.append("scale=-1:480:flags=lanczos")
        elif webp_scale == '360':
            v_filters.append("scale=-1:360:flags=lanczos")

        if v_filters:
            cmd.extend(['-vf', ",".join(v_filters)])

        cmd.extend([
            '-vcodec', 'libwebp',
            '-lossless', '0',
            '-compression_level', str(webp_compression),
            '-q:v', str(webp_quality),
            '-loop', '1',
            '-an'
        ])

        if strip_metadata:
            cmd.extend(['-map_metadata', '-1', '-map_chapters', '-1'])

        cmd.extend(['-progress', 'pipe:1', output_path])
        success = run_ffmpeg_with_progress(cmd, output_duration)
        return success, output_path

    if export_mode == 'copy' and speed_factor == 1.0 and current_rotation == 0 and crop_rect is None:
        cmd = [
            FFMPEG_PATH, '-n', '-nostdin',
            '-v', 'error',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', input_path,
        ]
        if include_audio:
            cmd.extend(['-c', 'copy', '-avoid_negative_ts', 'make_zero'])
        else:
            cmd.extend(['-c:v', 'copy', '-an', '-avoid_negative_ts', 'make_zero'])

        if strip_metadata:
            cmd.extend(['-map_metadata', '-1', '-map_chapters', '-1'])

        cmd.append(output_path)
        result = subprocess.run(cmd, creationflags=CREATION_FLAGS)
        return result.returncode == 0, output_path

    mode = export_mode if export_mode in presets else 'balanced'
    cmd = [
        FFMPEG_PATH, '-n', '-nostdin',
        '-v', 'error',
        '-ss', str(start_time),
        '-t', str(duration),
        '-i', input_path,
    ]

    v_filters = []
    if current_rotation == 90:
        v_filters.append("transpose=1")
    elif current_rotation == 180:
        v_filters.append("transpose=1,transpose=1")
    elif current_rotation == 270:
        v_filters.append("transpose=2")

    if crop_rect is not None:
        cx, cy, cw, ch = crop_rect
        v_filters.append(f"crop={cw}:{ch}:{cx}:{cy}")

    if speed_factor != 1.0:
        v_filters.append(f"setpts={1.0 / speed_factor}*(PTS-STARTPTS)")

    if v_filters:
        cmd.extend(['-filter:v', ",".join(v_filters)])

    cmd.extend(presets[mode]['v'])

    if not include_audio:
        cmd.append('-an')
    else:
        if speed_factor != 1.0:
            tempo_filters = ["asetpts=PTS-STARTPTS"]
            tempo = speed_factor
            while tempo < 0.5:
                tempo_filters.append("atempo=0.5")
                tempo /= 0.5
            while tempo > 2.0:
                tempo_filters.append("atempo=2.0")
                tempo /= 2.0
            tempo_filters.append(f"atempo={tempo}")
            cmd.extend(['-filter:a', ",".join(tempo_filters)])
        cmd.extend(presets[mode]['a'])

    if strip_metadata:
        cmd.extend(['-map_metadata', '-1', '-map_chapters', '-1'])

    cmd.extend(['-progress', 'pipe:1', output_path])
    success = run_ffmpeg_with_progress(cmd, output_duration)
    return success, output_path


def main():
    try:
        video_path = win_file_path('video', filetypes='video')
    except MissingInputError:
        show_console()
        ask_exit("No video file selected. Exiting.", timeout=5)
    base_output_path = video_path.parent / (str(video_path.stem) + '_cut.mp4')

    success, final_output_path = preview_and_cut(str(video_path), str(base_output_path))

    if success:
        audio_path = get_bundled_file_path(r'SourceFiles\au5-1.mp3')
        playsound(audio_path)
        final_path_obj = Path(final_output_path)
        if count_open_windows(final_path_obj.parent.name) == 0:
            os.startfile(str(final_path_obj))


if __name__ == '__main__':
    main()