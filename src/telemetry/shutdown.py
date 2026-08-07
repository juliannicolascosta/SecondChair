"""A content-free Windows signal for requesting a clean SecondChair shutdown."""

import ctypes


EVENT_MODIFY_STATE = 0x0002
WAIT_OBJECT_0 = 0
SECONDCHAIR_STOP_EVENT = "Local\\SecondChairStop"


class WindowsShutdownSignal:
    def __init__(self, kernel32=None):
        self.kernel32 = kernel32 or ctypes.windll.kernel32
        self._configure()
        self.handle = self.kernel32.CreateEventW(
            None,
            True,
            False,
            SECONDCHAIR_STOP_EVENT,
        )
        if not self.handle:
            raise OSError("Could not create SecondChair shutdown event")

    def _configure(self):
        self.kernel32.CreateEventW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_wchar_p,
        ]
        self.kernel32.CreateEventW.restype = ctypes.c_void_p
        self.kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        self.kernel32.WaitForSingleObject.restype = ctypes.c_uint
        self.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self.kernel32.CloseHandle.restype = ctypes.c_int

    def is_set(self):
        return self.kernel32.WaitForSingleObject(self.handle, 0) == WAIT_OBJECT_0

    def close(self):
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


def request_shutdown(kernel32=None):
    kernel32 = kernel32 or ctypes.windll.kernel32
    kernel32.OpenEventW.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.OpenEventW.restype = ctypes.c_void_p
    kernel32.SetEvent.argtypes = [ctypes.c_void_p]
    kernel32.SetEvent.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, SECONDCHAIR_STOP_EVENT)
    if not handle:
        return False
    try:
        return bool(kernel32.SetEvent(handle))
    finally:
        kernel32.CloseHandle(handle)
