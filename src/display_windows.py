"""Windows display power-off via SendMessage SC_MONITORPOWER."""

from __future__ import annotations

import ctypes
import platform
import sys
from dataclasses import dataclass
from enum import Enum, auto


class Backend(Enum):
    WIN32 = auto()


@dataclass(frozen=True)
class SessionInfo:
    backend: Backend
    session_type: str
    desktop: str
    label: str


HWND_BROADCAST = 0xFFFF
WM_SYSCOMMAND = 0x0112
SC_MONITORPOWER = 0xF170
MONITOR_OFF = 2


def detect_session() -> SessionInfo:
    ver = platform.version()
    return SessionInfo(
        Backend.WIN32,
        "windows",
        platform.platform(terse=True),
        f"Windows {ver} (SendMessage)",
    )


def turn_off() -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Windows backend only runs on win32"

    try:
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        result = user32.SendMessageW(
            HWND_BROADCAST,
            WM_SYSCOMMAND,
            SC_MONITORPOWER,
            MONITOR_OFF,
        )
        if result == 0:
            err = ctypes.get_last_error()
            if err:
                return False, f"SendMessage failed (error {err})"
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
