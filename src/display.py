"""Platform-specific display power-off API."""

from __future__ import annotations

import sys

if sys.platform == "win32":
    from display_windows import SessionInfo, detect_session, turn_off
else:
    from display_linux import SessionInfo, detect_session, turn_off

__all__ = ["SessionInfo", "detect_session", "turn_off"]
