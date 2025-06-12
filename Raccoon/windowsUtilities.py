from pathlib import Path
from tkinter import filedialog, Tk
import time
import msvcrt
import sys


def askExit(message: str, timeout: int = 5) -> None:
    print(message)
    print(f"Press any key to exit (or wait {timeout:.0f}s)…")

    start = time.time()
    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            break
        if time.time() - start >= timeout:
            break
        time.sleep(0.05)

    sys.exit()


def winDirPath(message: str) -> Path:
    root = Tk()
    root.withdraw()
    root.lift()

    file_path = Path(filedialog.askdirectory(title=message, parent=root))
    if not file_path:
        raise RaccoonErrors.MissingInputError('User closed the window')

    return file_path


def winFilePath(message: str, filetypes=None) -> Path:
    root = Tk()
    root.lift()
    root.withdraw()

    kwargs = {"title": message, "parent": root}
    if filetypes is not None:
        if filetypes == 'audio':
            selection = [
                ("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
                ("MP3 files", "*.MP3"),
                ("AAC files", "*.AAC"),
                ("FLAC files", "*.FLAC"),
                ("WAV files", "*.WAV"),
                ("PCM files", "*.PCM"),
                ("M4A files", "*.M4A"),
                ("OPUS files", "*.opus"),
            ]

            kwargs["filetypes"] = selection  # type: ignore[arg-type]
        elif filetypes == 'image':
            selection = [
                ("Image files", "*.PNG *.JPEG *.jpg"),
                ("PNG files", "*.PNG"),
                ("JPEG files", "*.JPEG"),
                ("JPG files", "*.jpg")
            ]
            kwargs["filetypes"] = selection  # type: ignore[arg-type]
        else:
            kwargs["filetypes"] = filetypes

    file_path_str = filedialog.askopenfilename(**kwargs)  # type: ignore[arg-type]
    file_path = Path(file_path_str)

    if not file_path_str:
        raise RaccoonErrors.MissingInputError('User closed the window')

    return file_path


def winFilesPath(message: str, filetypes=None) -> list[Path]:
    root = Tk()
    root.lift()
    root.withdraw()
    kwargs: list[tuple[str, str]] | Sequence[tuple[str, str]] = {"title": message, "parent": root}
    if filetypes is not None:
        if filetypes == 'audio':
            selection = [
                ("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus"),
                ("MP3 files", "*.MP3"),
                ("AAC files", "*.AAC"),
                ("FLAC files", "*.FLAC"),
                ("WAV files", "*.WAV"),
                ("PCM files", "*.PCM"),
                ("M4A files", "*.M4A"),
                ("OPUS files", "*.opus"),
            ]
            kwargs["filetypes"] = selection  # type: ignore[arg-type]
        elif filetypes == 'image':
            selection = cast(Sequence[Tuple[str, str]],
                             [
                                 ("Image files", "*.PNG *.JPEG"),
                                 ("PNG files", "*.PNG"),
                                 ("JPEG files", "*.JPEG")
                             ])
            kwargs["filetypes"] = selection  # type: ignore[arg-type]
        else:
            kwargs["filetypes"] = filetypes  # type: ignore[arg-type]

    file_paths = root.tk.splitlist(
        filedialog.askopenfilenames(**kwargs)  # type: ignore[arg-type]
    )
    root.destroy()

    if not file_paths:
        raise RaccoonErrors.MissingInputError("User closed the window")

    return [Path(p) for p in file_paths]


def count_open_windows(process_name: str) -> int or None:
    import psutil
    import pygetwindow as gw
    import win32gui
    import win32process
    open_windows = 0

    for window in gw.getAllWindows():
        hwnd = window.handle

        if not win32gui.IsWindowVisible(hwnd):
            continue

        cls = win32gui.GetClassName(hwnd)
        if cls not in ("CabinetWClass", "ExploreWClass"):
            continue

        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:
            proc = psutil.Process(pid)
            if proc.name().lower() == process_name:
                open_windows += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return open_windows
