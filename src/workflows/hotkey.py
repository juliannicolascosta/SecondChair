"""Global Windows hotkey used only to delimit a calibration interval."""

import ctypes
from ctypes import wintypes
from threading import Event, Thread


WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_NOREPEAT = 0x4000
VK_F8 = 0x77
HOTKEY_ID = 0x5343


class WindowsCalibrationHotkey:
    def __init__(self, user32=None, key=VK_F8):
        self.user32 = user32 or ctypes.windll.user32
        self.key = key
        self._callback = None
        self._thread = None
        self._thread_id = None
        self._ready = Event()
        self.error = None

    def start(self, callback):
        if self._thread and self._thread.is_alive():
            return
        self._callback = callback
        self.error = None
        self._ready.clear()
        self._thread = Thread(target=self._run, daemon=True, name="calibration-hotkey")
        self._thread.start()
        self._ready.wait(timeout=2)
        if self.error is not None:
            raise self.error

    def stop(self):
        if self._thread_id is not None:
            self.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._thread = None
        self._thread_id = None

    def _run(self):
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        if not self.user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, self.key):
            self.error = OSError("Could not register global F8 calibration hotkey")
            self._ready.set()
            return
        self._ready.set()
        try:
            message = wintypes.MSG()
            while self.user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                    self._callback()
        finally:
            self.user32.UnregisterHotKey(None, HOTKEY_ID)
