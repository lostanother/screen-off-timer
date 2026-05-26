#!/usr/bin/env python3
"""Screen-off timer — Windows tkinter GUI."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from display import detect_session, turn_off

MAX_SECONDS = 86400


def _resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _icon_path() -> Path | None:
    root = _resource_root()
    ico = root / "data" / "icons" / "screen-off-timer.ico"
    if ico.is_file():
        return ico
    png = root / "data" / "icons" / "hicolor" / "256x256" / "apps" / "screen-off-timer.png"
    return png if png.is_file() else None


class ScreenOffTimerWin:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("延时熄屏")
        self.root.resizable(False, False)
        self.root.minsize(360, 220)

        icon = _icon_path()
        if icon and icon.suffix.lower() == ".ico":
            try:
                self.root.iconbitmap(default=str(icon))
            except tk.TclError:
                pass

        self._remaining = 0
        self._timer_id: str | None = None
        self._info = detect_session()

        pad = {"padx": 20, "pady": 8}
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            frm,
            text=f"当前环境: {self._info.label}",
            wraplength=320,
        ).grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        row = ttk.Frame(frm)
        row.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        self._seconds = tk.IntVar(value=60)
        self._spin = ttk.Spinbox(
            row,
            from_=1,
            to=MAX_SECONDS,
            textvariable=self._seconds,
            width=10,
        )
        self._spin.grid(row=0, column=0, padx=(0, 8))
        ttk.Label(row, text="秒后熄屏").grid(row=0, column=1)

        self._status = ttk.Label(frm, text="就绪")
        self._status.grid(row=2, column=0, columnspan=2, sticky="w", **pad)

        btn_row = ttk.Frame(frm)
        btn_row.grid(row=3, column=0, columnspan=2, sticky="e", **pad)

        self._cancel_btn = ttk.Button(btn_row, text="取消", command=self._on_cancel, state="disabled")
        self._cancel_btn.grid(row=0, column=0, padx=4)

        self._start_btn = ttk.Button(btn_row, text="开始", command=self._on_start)
        self._start_btn.grid(row=0, column=1, padx=4)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_countdown_ui(self, active: bool) -> None:
        self._spin.configure(state="disabled" if active else "normal")
        self._start_btn.configure(state="disabled" if active else "normal")
        self._cancel_btn.configure(state="normal" if active else "disabled")

    def _on_start(self) -> None:
        try:
            seconds = int(self._seconds.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("无法熄屏", "请输入有效的秒数。")
            return
        if seconds < 1:
            messagebox.showerror("无法熄屏", "请输入大于 0 的秒数。")
            return

        self._remaining = seconds
        self._set_countdown_ui(True)
        self._update_status()
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
        self._timer_id = self.root.after(1000, self._tick)

    def _on_cancel(self) -> None:
        self._stop_timer()
        self._status.configure(text="已取消")
        self._set_countdown_ui(False)

    def _on_close(self) -> None:
        self._stop_timer()
        self.root.destroy()

    def _stop_timer(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._remaining = 0

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining > 0:
            self._update_status()
            self._timer_id = self.root.after(1000, self._tick)
            return

        self._stop_timer()
        self._set_countdown_ui(False)
        self._status.configure(text="正在熄屏…")
        self.root.update_idletasks()

        ok, err = turn_off()
        self._status.configure(text="就绪" if ok else "熄屏失败")
        if not ok:
            messagebox.showerror("无法熄屏", err)

    def _update_status(self) -> None:
        self._status.configure(text=f"剩余 {self._remaining} 秒")

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main() -> int:
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    return ScreenOffTimerWin().run()


if __name__ == "__main__":
    raise SystemExit(main())
