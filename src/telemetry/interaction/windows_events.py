"""Windows event hooks that expose action categories, never key or pointer data."""

import ctypes
from ctypes import wintypes
from threading import Event, Thread

from src.telemetry.interaction.models import InteractionType


WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207
WM_MOUSEWHEEL = 0x020A
WM_MOUSEHWHEEL = 0x020E
WM_QUIT = 0x0012


class WindowsEventSource:
    """Emit only coarse action categories from a dedicated Windows message loop.

    The callback intentionally never dereferences ``l_param``. Consequently key
    identity, typed text, pointer coordinates and wheel deltas never enter Python.
    """

    def __init__(self, user32=None):
        self.user32 = user32 or getattr(ctypes, "windll", None).user32
        self._thread = None
        self._thread_id = None
        self._ready = Event()
        self._callback = None
        self._hooks = []

    def start(self, callback):
        if self._thread and self._thread.is_alive():
            return
        self._callback = callback
        self._thread = Thread(target=self._run, daemon=True, name="interaction-telemetry")
        self._thread.start()
        self._ready.wait(timeout=2)

    def stop(self):
        if self._thread_id is not None:
            self.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._thread = None
        self._thread_id = None

    def _run(self):
        kernel32 = ctypes.windll.kernel32
        self.user32.SetWindowsHookExW.restype = ctypes.c_void_p
        self.user32.CallNextHookEx.restype = ctypes.c_ssize_t
        kernel32.GetModuleHandleW.restype = ctypes.c_void_p
        self._thread_id = kernel32.GetCurrentThreadId()
        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        def keyboard_callback(code, message, opaque_data):
            if code >= 0 and message in (WM_KEYDOWN, WM_SYSKEYDOWN):
                self._callback(InteractionType.KEYBOARD_ACTIVITY)
            return self.user32.CallNextHookEx(None, code, message, opaque_data)

        def mouse_callback(code, message, opaque_data):
            if code >= 0:
                if message in (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN):
                    self._callback(InteractionType.MOUSE_CLICK)
                elif message in (WM_MOUSEWHEEL, WM_MOUSEHWHEEL):
                    self._callback(InteractionType.SCROLL)
            return self.user32.CallNextHookEx(None, code, message, opaque_data)

        # Keep references alive for the lifetime of the native hooks.
        self._native_callbacks = (
            callback_type(keyboard_callback),
            callback_type(mouse_callback),
        )
        module = kernel32.GetModuleHandleW(None)
        self._hooks = [
            self.user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._native_callbacks[0], module, 0),
            self.user32.SetWindowsHookExW(WH_MOUSE_LL, self._native_callbacks[1], module, 0),
        ]
        self._ready.set()

        message = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            self.user32.TranslateMessage(ctypes.byref(message))
            self.user32.DispatchMessageW(ctypes.byref(message))

        for hook in self._hooks:
            if hook:
                self.user32.UnhookWindowsHookEx(hook)
        self._hooks = []
