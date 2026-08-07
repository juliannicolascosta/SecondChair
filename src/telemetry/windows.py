"""
Second Chair

Módulo:
Telemetry

Archivo:
windows.py

Responsabilidad:
Obtener información de la ventana activa de Windows.
"""

import ctypes
from pathlib import Path

try:
    import pygetwindow as gw
except ImportError:  # Tests and non-Windows analytics remain importable.
    gw = None


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_idle_seconds(user32=None, kernel32=None):
    """Return elapsed seconds since input without reading which input occurred."""

    user32 = user32 or ctypes.windll.user32
    kernel32 = kernel32 or ctypes.windll.kernel32
    info = LASTINPUTINFO(cbSize=ctypes.sizeof(LASTINPUTINFO))
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0
    elapsed_ms = (kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
    return elapsed_ms // 1000


def _process_name(window):
    """Read only the executable name associated with a window handle."""

    handle = getattr(window, "_hWnd", None)
    if not handle or not getattr(ctypes, "windll", None):
        return None
    process_id = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
    process = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        process_id.value,
    )
    if not process:
        return None
    try:
        size = ctypes.c_ulong(32768)
        path = ctypes.create_unicode_buffer(size.value)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(
            process,
            0,
            path,
            ctypes.byref(size),
        ):
            return Path(path.value).name
    finally:
        ctypes.windll.kernel32.CloseHandle(process)
    return None


def get_active_window():

    if gw is None:
        raise RuntimeError("PyGetWindow is required for live Windows telemetry")

    window = gw.getActiveWindow()

    if window is None:
        return None

    process_name = _process_name(window)
    return {
        "title": window.title,
        "process_name": process_name,
        "application": Path(process_name).stem if process_name else None,
    }
