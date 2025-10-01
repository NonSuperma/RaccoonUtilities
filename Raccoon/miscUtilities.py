import sys, os

def seconds_to_hhmmss(s: float) -> str:
    sign = "-" if s < 0 else ""
    s = abs(s)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f'{sign}{h:02d}:{m:02d}:{sec:06.3f}'


def hhmmss_to_seconds(timestamp: str) -> float:
    parts = timestamp.split(':')
    if len(parts) != 3:
        raise ValueError(f"Invalid format: expected 'HH:MM:SS.sss', got '{timestamp}'")

    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return hours * 3600 + minutes * 60 + seconds


def add_times(time_list: list[str] or list[float]) -> str:
    total = 0
    _format = 's' if time_list is list[str] else 'hh'
    for t in time_list:
        if _format == 's':
            total += t
        else:
            total += hhmmss_to_seconds(t)
    return seconds_to_hhmmss(total)

def resource_path(relative_path: str) -> str:

    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
