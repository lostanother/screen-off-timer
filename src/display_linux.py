"""Linux display power-off backends."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable


class Backend(Enum):
    X11 = auto()
    GNOME = auto()
    KDE = auto()
    WLROOTS = auto()
    UNSUPPORTED = auto()


@dataclass(frozen=True)
class SessionInfo:
    backend: Backend
    session_type: str
    desktop: str
    label: str


def _env_desktop() -> str:
    return (
        os.environ.get("XDG_CURRENT_DESKTOP", "")
        or os.environ.get("XDG_SESSION_DESKTOP", "")
    ).lower()


def _env_session_type() -> str:
    return os.environ.get("XDG_SESSION_TYPE", "").lower()


def _desktop_contains(*needles: str) -> bool:
    desktop = _env_desktop()
    return any(n in desktop for n in needles)


def detect_session() -> SessionInfo:
    session_type = _env_session_type() or "unknown"
    desktop = _env_desktop() or "unknown"

    if session_type == "x11":
        return SessionInfo(Backend.X11, session_type, desktop, "X11 (xset dpms)")

    if session_type == "wayland":
        if _desktop_contains("gnome", "ubuntu", "unity", "cinnamon"):
            return SessionInfo(
                Backend.GNOME, session_type, desktop, "GNOME / Mutter (busctl)"
            )
        if _desktop_contains("kde", "plasma"):
            return SessionInfo(
                Backend.KDE, session_type, desktop, "KDE Plasma (kscreen-doctor)"
            )
        if _desktop_contains("sway", "hyprland", "wlroots", "river", "niri"):
            return SessionInfo(
                Backend.WLROOTS, session_type, desktop, "wlroots (wlr-dpms)"
            )

    return SessionInfo(
        Backend.UNSUPPORTED, session_type, desktop, "unsupported session"
    )


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, check=False
        )
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, f"command timed out: {cmd[0]}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, detail or f"exit code {result.returncode}"
    return True, ""


def _resolve(cmd: str) -> str | None:
    return shutil.which(cmd)


def _turn_off_x11() -> tuple[bool, str]:
    xset = _resolve("xset")
    if not xset:
        return False, "xset not found (install x11-xserver-utils)"
    return _run([xset, "dpms", "force", "off"])


def _turn_off_gnome() -> tuple[bool, str]:
    busctl = _resolve("busctl")
    if not busctl:
        return False, "busctl not found"
    return _run(
        [
            busctl,
            "--user",
            "set-property",
            "org.gnome.Mutter.DisplayConfig",
            "/org/gnome/Mutter/DisplayConfig",
            "org.gnome.Mutter.DisplayConfig",
            "PowerSaveMode",
            "i",
            "3",
        ]
    )


def _turn_off_kde() -> tuple[bool, str]:
    doctor = _resolve("kscreen-doctor")
    if not doctor:
        return False, "kscreen-doctor not found"
    return _run([doctor, "--dpms", "off"])


def _turn_off_wlroots() -> tuple[bool, str]:
    wlr_dpms = _resolve("wlr-dpms")
    if not wlr_dpms:
        return False, "wlr-dpms not found"
    return _run([wlr_dpms, "off"])


_BACKENDS: dict[Backend, Callable[[], tuple[bool, str]]] = {
    Backend.X11: _turn_off_x11,
    Backend.GNOME: _turn_off_gnome,
    Backend.KDE: _turn_off_kde,
    Backend.WLROOTS: _turn_off_wlroots,
}


def turn_off() -> tuple[bool, str]:
    info = detect_session()
    handler = _BACKENDS.get(info.backend)
    if handler is None:
        return (
            False,
            "Unsupported desktop environment.\n"
            f"  XDG_SESSION_TYPE={info.session_type}\n"
            f"  XDG_CURRENT_DESKTOP={info.desktop}\n\n"
            "Supported: X11, GNOME Wayland, KDE, wlroots.",
        )
    ok, err = handler()
    if not ok:
        return False, f"{info.label} failed: {err}"
    return True, ""
