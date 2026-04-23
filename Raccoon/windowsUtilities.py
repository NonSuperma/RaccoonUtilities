from Raccoon.errors import *
from pathlib import Path
from tkinter import filedialog, Tk
import ctypes
from ctypes import wintypes
import time
import msvcrt
import sys


def ask_exit(message: str = '', timeout: int = 5) -> None:
    print(message)
    print(f'Press any key to exit (or wait {timeout} more seconds)')
    start = time.monotonic()
    last_shown = None

    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            break

        elapsed = time.monotonic() - start
        remaining = max(0, int(timeout - elapsed))

        if remaining != last_shown:
            print(f"\033[F\033[K"  # Move curson up, to beginning of line and clear line
                  f"Press any key to exit "
                  f"(or wait {remaining} more seconds)…")
            last_shown = remaining

        if elapsed >= timeout:
            break

        time.sleep(0.05)

    sys.exit()


def win_dir_path(message: str = '') -> Path:
    root = Tk()
    root.withdraw()
    root.lift()

    kwargs = {"title": message, "parent": root}
    if initialDir is not None:
        kwargs["initialdir"] = str(initialDir)

    dir_path = Path(filedialog.askdirectory(**kwargs))

    if not dir_path:
        raise MissingInputError('User closed the window')

    return dir_path


def win_dirs_path(title: str = '') -> list[Path]:
    _ole32 = ctypes.oledll.ole32
    _user32 = ctypes.windll.user32

    CLSID_FileOpenDialog = "{DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7}"
    IID_IFileOpenDialog = "{D57C7288-D4AD-4768-BE02-9D969532D960}"

    FOS_PICKFOLDERS = 0x20
    FOS_ALLOWMULTISELECT = 0x200
    FOS_NOVALIDATE = 0x100
    FOS_NOTESTFILECREATE = 0x10000
    FOS_DONTADDTORECENT = 0x2000000

    FINAL_FLAGS = (FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT |
                   FOS_NOVALIDATE | FOS_NOTESTFILECREATE | FOS_DONTADDTORECENT)

    SIGDN_DESKTOPABSOLUTEPARSING = 0x80028000

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", ctypes.c_ulong),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8)]

    def create_guid(guid_str):
        guid = GUID()
        _ole32.CLSIDFromString(ctypes.c_wchar_p(guid_str), ctypes.byref(guid))
        return guid

    class IUnknown(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.POINTER(ctypes.c_void_p))]

    class IFileOpenDialog(IUnknown):
        pass

    def _err(hresult):
        if hresult < 0:
            raise ctypes.WinError(hresult)

    try:
        _ole32.CoInitialize(None)

        pfd = ctypes.POINTER(IFileOpenDialog)()
        guid_clsid = create_guid(CLSID_FileOpenDialog)
        guid_iid = create_guid(IID_IFileOpenDialog)

        _err(_ole32.CoCreateInstance(
            ctypes.byref(guid_clsid),
            None,
            1,
            ctypes.byref(guid_iid),
            ctypes.byref(pfd)
        ))

        vtbl = ctypes.cast(pfd.contents.lpVtbl, ctypes.POINTER(ctypes.c_void_p))

        SetOptions = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint)(vtbl[9])
        _err(SetOptions(pfd, FINAL_FLAGS))

        SetTitle = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_wchar_p)(vtbl[17])
        if title:
            _err(SetTitle(pfd, title))

        hwnd_owner = _user32.GetForegroundWindow()
        Show = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(vtbl[3])
        hr = Show(pfd, hwnd_owner)

        if hr < 0:
            return []

        GetResults = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(vtbl[27])
        psi_results = ctypes.c_void_p()
        _err(GetResults(pfd, ctypes.byref(psi_results)))

        vtbl_results = ctypes.cast(
            ctypes.cast(psi_results, ctypes.POINTER(ctypes.c_void_p)).contents,
            ctypes.POINTER(ctypes.c_void_p)
        )

        GetCount = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint))(vtbl_results[7])
        count = ctypes.c_uint()
        _err(GetCount(psi_results, ctypes.byref(count)))

        paths = []
        GetItemAt = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p))(
            vtbl_results[8])

        for i in range(count.value):
            psi_item = ctypes.c_void_p()
            _err(GetItemAt(psi_results, i, ctypes.byref(psi_item)))

            vtbl_item = ctypes.cast(
                ctypes.cast(psi_item, ctypes.POINTER(ctypes.c_void_p)).contents,
                ctypes.POINTER(ctypes.c_void_p)
            )

            GetDisplayName = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint,
                                                ctypes.POINTER(ctypes.c_wchar_p))(vtbl_item[5])
            p_path = ctypes.c_wchar_p()

            _err(GetDisplayName(psi_item, SIGDN_DESKTOPABSOLUTEPARSING, ctypes.byref(p_path)))

            final_path = Path(p_path.value)
            if final_path.is_dir():
                paths.append(final_path)

            _ole32.CoTaskMemFree(p_path)

        return paths

    finally:
        _ole32.CoUninitialize()


def win_file_path(message: str = '', filetypes=None, initialDir: Path = None) -> Path:
    root = Tk()
    root.attributes('-topmost', True)
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

    if initialDir is not None:
        kwargs["initialdir"] = str(initialDir)
    file_path_str = filedialog.askopenfilename(**kwargs)  # type: ignore[arg-type]
    file_path = Path(file_path_str)

    if not file_path_str:
        raise MissingInputError('User closed the window')

    return file_path


def win_files_path(message: str = '', filetypes=None, initialDir: Path = None) -> list[Path]:
    root = Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    kwargs = {"title": message, "parent": root}
    if filetypes is not None:
        if filetypes == 'audio':
            selection = [
                ("Audio files", "*.MP3 *.AAC *.FLAC *.WAV *.PCM *.M4A *.opus *.ogg"),
                ("MP3 files", "*.MP3"),
                ("AAC files", "*.AAC"),
                ("FLAC files", "*.FLAC"),
                ("WAV files", "*.WAV"),
                ("PCM files", "*.PCM"),
                ("M4A files", "*.M4A"),
                ("OPUS files", "*.opus"),
                ("OGG files", "*.ogg"),
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

    if initialDir is not None:
        kwargs["initialdir"] = str(initialDir)

    file_paths = root.tk.splitlist(
        filedialog.askopenfilenames(**kwargs)  # type: ignore[arg-type]
    )
    root.destroy()

    if not file_paths:
        raise MissingInputError("User closed the window")

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


def file_is_in_dir(file_name: str, dir_path: Path) -> bool:
    if any(x.name == file_name for x in list(dir_path.iterdir())):
        return True
    else:
        return False
