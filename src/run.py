#!/usr/bin/env python3
"""Cross-platform entry point."""

from __future__ import annotations

import sys


def main() -> int:
    if sys.platform == "win32":
        from main_win import main as win_main

        return win_main()
    from main import main as linux_main

    return linux_main()


if __name__ == "__main__":
    raise SystemExit(main())
