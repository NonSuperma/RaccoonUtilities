import ctypes
import msvcrt
import sys
import time
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Sequence

import pygetwindow as gw
import win32gui
from Raccoon.errors import MissingInputError

FileTypeSpec = Sequence[tuple[str, str]] | str | None

FILETYPE_PRESETS: dict[str, Sequence[tuple[str, str]]] = {
    "audio": (
        ("Audio files", "*.mp3 *.aac *.flac *.wav *.pcm *.m4a *.opus *.ogg"),
        ("MP3 files", "*.mp3"),
        ("AAC files", "*.aac"),
        ("FLAC files", "*.flac"),
        ("WAV files", "*.wav"),
        ("PCM files", "*.pcm"),
        ("M4A files", "*.m4a"),
        ("OPUS files", "*.opus"),
        ("OGG files", "*.ogg"),
    ),
    "image": (
        ("Image files", "*.png *.jpeg *.jpg *.webp *.bmp"),
        ("PNG files", "*.png"),
        ("JPEG files", "*.jpeg *.jpg"),
        ("WEBP files", "*.webp"),
        ("BMP files", "*.bmp"),
    ),
    "video": (
        ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv"),
        ("MP4 files", "*.mp4"),
        ("AVI files", "*.avi"),
        ("MKV files", "*.mkv"),
        ("MOV files", "*.mov"),
        ("WMV files", "*.wmv"),
    )
}

_OLE32 = ctypes.oledll.ole32
_USER32 = ctypes.windll.user32
_CLSID_FILE_OPEN_DIALOG = "{DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7}"
_IID_IFILE_OPEN_DIALOG = "{D57C7288-D4AD-4768-BE02-9D969532D960}"
_FOS_FLAGS = 0x20 | 0x200 | 0x100 | 0x10000 | 0x2000000
_SIGDN_DESKTOPABSOLUTEPARSING = 0x80028000


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _IUnknown(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]


class _IFileOpenDialog(_IUnknown):
    pass


def _create_guid(guid_str: str) -> _GUID:
    guid = _GUID()
    _OLE32.CLSIDFromString(ctypes.c_wchar_p(guid_str), ctypes.byref(guid))
    return guid


def _check_hresult(hr: int) -> None:
    if hr < 0:
        raise ctypes.WinError(hr)


def _resolve_filetypes(filetypes: FileTypeSpec) -> Sequence[tuple[str, str]] | None:
    if isinstance(filetypes, str):
        return FILETYPE_PRESETS.get(filetypes.lower(), (("All files", "*.*"),))
    return filetypes


def _create_tk_root() -> Tk:
    root = Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    return root


def ask_exit(message: str = "", timeout: int = 5) -> None:
    print(message)
    print(f"Press any key to exit (or wait {timeout} more seconds)")
    start = time.monotonic()
    last_shown = None

    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            break

        elapsed = time.monotonic() - start
        remaining = max(0, int(timeout - elapsed))

        if remaining != last_shown:
            print(
                f"\033[F\033[K"
                f"Press any key to exit (or wait {remaining} more seconds)…"
            )
            last_shown = remaining

        if elapsed >= timeout:
            break

        time.sleep(0.05)

    sys.exit()


def win_dir_path(message: str = "", initial_dir: Path | None = None) -> Path:
    root = _create_tk_root()
    kwargs = {"title": message, "parent": root}
    if initial_dir is not None:
        kwargs["initialdir"] = str(initial_dir)

    dir_str = filedialog.askdirectory(**kwargs)
    root.destroy()

    if not dir_str:
        raise MissingInputError("User closed the window")

    return Path(dir_str)


def win_dirs_path(title: str = "") -> list[Path]:
    try:
        _OLE32.CoInitialize(None)

        pfd = ctypes.POINTER(_IFileOpenDialog)()
        clsid = _create_guid(_CLSID_FILE_OPEN_DIALOG)
        iid = _create_guid(_IID_IFILE_OPEN_DIALOG)

        _check_hresult(
            _OLE32.CoCreateInstance(
                ctypes.byref(clsid),
                None,
                1,
                ctypes.byref(iid),
                ctypes.byref(pfd),
            )
        )

        vtbl = ctypes.cast(pfd.contents.lpVtbl, ctypes.POINTER(ctypes.c_void_p))

        set_options = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.c_uint
        )(vtbl[9])
        _check_hresult(set_options(pfd, _FOS_FLAGS))

        if title:
            set_title = ctypes.WINFUNCTYPE(
                ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p
            )(vtbl[17])
            _check_hresult(set_title(pfd, title))

        hwnd_owner = _USER32.GetForegroundWindow()
        show = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p
        )(vtbl[3])
        if show(pfd, hwnd_owner) < 0:
            return []

        get_results = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
        )(vtbl[27])
        psi_results = ctypes.c_void_p()
        _check_hresult(get_results(pfd, ctypes.byref(psi_results)))

        vtbl_results = ctypes.cast(
            ctypes.cast(psi_results, ctypes.POINTER(ctypes.c_void_p)).contents,
            ctypes.POINTER(ctypes.c_void_p),
        )

        get_count = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)
        )(vtbl_results[7])
        count = ctypes.c_uint()
        _check_hresult(get_count(psi_results, ctypes.byref(count)))

        paths: list[Path] = []
        get_item_at = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_void_p),
        )(vtbl_results[8])

        for i in range(count.value):
            psi_item = ctypes.c_void_p()
            _check_hresult(get_item_at(psi_results, i, ctypes.byref(psi_item)))

            vtbl_item = ctypes.cast(
                ctypes.cast(psi_item, ctypes.POINTER(ctypes.c_void_p)).contents,
                ctypes.POINTER(ctypes.c_void_p),
            )

            get_display_name = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.POINTER(ctypes.c_wchar_p),
            )(vtbl_item[5])
            p_path = ctypes.c_wchar_p()

            _check_hresult(
                get_display_name(
                    psi_item, _SIGDN_DESKTOPABSOLUTEPARSING, ctypes.byref(p_path)
                )
            )

            final_path = Path(p_path.value)
            if final_path.is_dir():
                paths.append(final_path)

            _OLE32.CoTaskMemFree(p_path)

        return paths

    finally:
        _OLE32.CoUninitialize()


def win_file_path(
    message: str = "",
    filetypes: FileTypeSpec = None,
    initial_dir: Path | None = None,
) -> Path:

    root = _create_tk_root()
    kwargs = {
        "title": message,
        "parent": root,
        "filetypes": _resolve_filetypes(filetypes),
    }
    if initial_dir is not None:
        kwargs["initialdir"] = str(initial_dir)

    file_path_str = filedialog.askopenfilename(**kwargs)
    root.destroy()

    if not file_path_str:
        raise MissingInputError("User closed the window")

    return Path(file_path_str)


def win_files_path(
    message: str = "",
    filetypes: FileTypeSpec = None,
    initial_dir: Path | None = None,
) -> list[Path]:

    root = _create_tk_root()
    kwargs = {
        "title": message,
        "parent": root,
        "filetypes": _resolve_filetypes(filetypes),
    }
    if initial_dir is not None:
        kwargs["initialdir"] = str(initial_dir)

    file_paths = root.tk.splitlist(filedialog.askopenfilenames(**kwargs))
    root.destroy()

    if not file_paths:
        raise MissingInputError("User closed the window")

    return [Path(p) for p in file_paths]


def count_open_windows(folder_name: str) -> int:
    open_windows = 0
    target = folder_name.lower()

    for window in gw.getAllWindows():
        hwnd = window._hWnd

        if not win32gui.IsWindowVisible(hwnd):
            continue

        cls = win32gui.GetClassName(hwnd)
        if cls not in ("CabinetWClass", "ExploreWClass"):
            continue

        if window.title.lower() == target:
            open_windows += 1

    return open_windows


def file_is_in_dir(file_name: str, dir_path: Path) -> bool:
    return any(p.name == file_name for p in dir_path.iterdir())