from pathlib import Path
import os
import sys
import subprocess
import ctypes
from playsound3 import playsound
from Raccoon.windowsUtilities import win_file_path, count_open_windows, ask_exit
from Raccoon.miscUtilities import seconds_to_hhmmss, get_bundled_file_path
from Raccoon.errors import MissingInputError

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
        keepaspect_window=True,
        snap_window=True,
        volume=60,
        volume_max=150,
        cache='yes',
        demuxer_max_bytes='1024MiB',
        demuxer_max_back_bytes='512MiB',
        demuxer_readahead_secs=60,
        hr_seek='yes',
        hr_seek_framedrop='no'
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
            lines = [
                "=== OPTIONS MENU ===",
                f"[1] Audio: {audio_checkbox}",
                f"[2] Strip Metadata: {metadata_checkbox}",
                f"[3] Speed: {speed_display} >",
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
        else:
            lines = ["S (Start) | E (End) | \nQ (Direct Copy) | Alt+Q (Re-encode) |\nO (Options)"]
            if start_marked:
                lines.append(f'Start marked at: {seconds_to_hhmmss(start_time)}')
            if end_time is not None:
                lines.append(f'End marked at:   {seconds_to_hhmmss(end_time)}')
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

    @player.on_key_press('o')
    def on_press_o():
        open_options_menu()

    @player.on_key_press('O')
    def on_press_upper_o():
        open_options_menu()

    @player.on_key_press('1')
    def select_one():
        nonlocal active_menu, include_audio, speed_factor
        if active_menu == 'encode':
            trigger_cut('ultrafast')
        elif active_menu == 'options':
            include_audio = not include_audio
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.25
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('2')
    def select_two():
        nonlocal active_menu, strip_metadata, speed_factor
        if active_menu == 'encode':
            trigger_cut('balanced')
        elif active_menu == 'options':
            strip_metadata = not strip_metadata
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.50
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('3')
    def select_three():
        nonlocal active_menu, speed_factor
        if active_menu == 'encode':
            trigger_cut('slow')
        elif active_menu == 'options':
            active_menu = 'speed'
            update_overlay()
        elif active_menu == 'speed':
            speed_factor = 0.75
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('4')
    def select_four():
        nonlocal active_menu, speed_factor
        if active_menu == 'speed':
            speed_factor = 1.0
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('5')
    def select_five():
        nonlocal active_menu, speed_factor
        if active_menu == 'speed':
            speed_factor = 1.25
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('6')
    def select_six():
        nonlocal active_menu, speed_factor
        if active_menu == 'speed':
            speed_factor = 1.50
            active_menu = 'options'
            update_overlay()

    @player.on_key_press('esc')
    def cancel_menu():
        nonlocal active_menu
        if active_menu == 'speed':
            active_menu = 'options'
        elif active_menu in ('encode', 'options'):
            active_menu = None
        update_overlay()

    @player.on_key_press('Alt+r')
    def rotate_clockwise():
        nonlocal current_rotation
        current_rotation = (current_rotation + 90) % 360
        player['video-rotate'] = current_rotation

    @player.on_key_press('Alt+R')
    def rotate_counter_clockwise():
        nonlocal current_rotation
        current_rotation = (current_rotation - 90) % 360
        player['video-rotate'] = current_rotation

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

    if export_mode == 'copy' and speed_factor == 1.0 and current_rotation == 0:
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
    if speed_factor != 1.0:
        v_filters.append(f"setpts={1.0 / speed_factor}*(PTS-STARTPTS)")
    if current_rotation == 90:
        v_filters.append("transpose=1")
    elif current_rotation == 180:
        v_filters.append("transpose=1,transpose=1")
    elif current_rotation == 270:
        v_filters.append("transpose=2")

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