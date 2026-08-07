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

import pygetwindow as gw


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


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

    window = gw.getActiveWindow()

    if window is None:
        return None

    process_name = _process_name(window)
    return {
        "title": window.title,
        "process_name": process_name,
        "application": Path(process_name).stem if process_name else None,
    }
