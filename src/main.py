#!/usr/bin/env python3
"""Screen-off timer — GTK 4 GUI."""

from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from display import detect_session, turn_off

APP_ID = "com.example.ScreenOffTimer"
MAX_SECONDS = 86400


class ScreenOffTimerApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self._remaining: int = 0
        self._timer_id: int | None = None
        self._spin: Gtk.SpinButton | None = None
        self._status: Gtk.Label | None = None
        self._start_btn: Gtk.Button | None = None
        self._cancel_btn: Gtk.Button | None = None
        self._session_label: Gtk.Label | None = None

    def do_activate(self) -> None:
        win = Gtk.ApplicationWindow(application=self, title="延时熄屏")
        win.set_default_size(360, 220)
        win.set_resizable(False)

        info = detect_session()

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main.set_margin_top(20)
        main.set_margin_bottom(20)
        main.set_margin_start(20)
        main.set_margin_end(20)
        win.set_child(main)

        session_label = Gtk.Label()
        session_label.set_markup(
            f"<span size='small'>当前环境: <b>{GLib.markup_escape_text(info.label)}</b></span>"
        )
        session_label.set_halign(Gtk.Align.START)
        session_label.set_wrap(True)
        self._session_label = session_label
        main.append(session_label)

        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        main.append(input_row)

        spin = Gtk.SpinButton()
        spin.set_adjustment(
            Gtk.Adjustment.new(60.0, 1.0, float(MAX_SECONDS), 1.0, 10.0, 0.0)
        )
        spin.set_numeric(True)
        spin.set_digits(0)
        self._spin = spin
        input_row.append(spin)

        sec_label = Gtk.Label(label="秒后熄屏")
        sec_label.set_halign(Gtk.Align.START)
        input_row.append(sec_label)

        self._status = Gtk.Label(label="就绪")
        self._status.set_halign(Gtk.Align.START)
        main.append(self._status)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.set_halign(Gtk.Align.END)
        main.append(btn_row)

        cancel_btn = Gtk.Button(label="取消")
        cancel_btn.set_sensitive(False)
        cancel_btn.connect("clicked", self._on_cancel)
        self._cancel_btn = cancel_btn
        btn_row.append(cancel_btn)

        start_btn = Gtk.Button(label="开始")
        start_btn.add_css_class("suggested-action")
        start_btn.connect("clicked", self._on_start)
        self._start_btn = start_btn
        btn_row.append(start_btn)

        win.connect("close-request", self._on_window_close)
        win.present()

    def _set_countdown_ui(self, active: bool) -> None:
        if self._spin:
            self._spin.set_sensitive(not active)
        if self._start_btn:
            self._start_btn.set_sensitive(not active)
        if self._cancel_btn:
            self._cancel_btn.set_sensitive(active)

    def _on_start(self, _button: Gtk.Button) -> None:
        if self._spin is None:
            return
        seconds = int(self._spin.get_value())
        if seconds < 1:
            self._show_error("请输入大于 0 的秒数。")
            return

        self._remaining = seconds
        self._set_countdown_ui(True)
        self._update_status()
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
        self._timer_id = GLib.timeout_add_seconds(1, self._tick)

    def _on_cancel(self, _button: Gtk.Button) -> None:
        self._stop_timer()
        if self._status:
            self._status.set_text("已取消")
        self._set_countdown_ui(False)

    def _on_window_close(self, _win: Gtk.ApplicationWindow) -> bool:
        self._stop_timer()
        return False

    def _stop_timer(self) -> None:
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None
        self._remaining = 0

    def _tick(self) -> bool:
        self._remaining -= 1
        if self._remaining > 0:
            self._update_status()
            return True

        self._stop_timer()
        self._set_countdown_ui(False)
        if self._status:
            self._status.set_text("正在熄屏…")

        ok, err = turn_off()
        if self._status:
            self._status.set_text("就绪" if ok else "熄屏失败")
        if not ok:
            self._show_error(err)
        return False

    def _update_status(self) -> None:
        if self._status:
            self._status.set_text(f"剩余 {self._remaining} 秒")

    def _show_error(self, message: str) -> None:
        dialog = Gtk.AlertDialog()
        dialog.set_message("无法熄屏")
        dialog.set_detail(message)
        dialog.set_modal(True)
        if win := self.get_active_window():
            dialog.show(win)


def main() -> int:
    app = ScreenOffTimerApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
