"""Translucent on-screen display (OSD) overlay for knob activity.

Shows a small two-line popup in the bottom-right corner (over the taskbar) on
every knob gesture: line 1 = the gesture, line 2 = the bound action. Driven
entirely on the Tk main thread; the worker thread calls show() which marshals
the real work via root.after(0, ...).
"""
import tkinter as tk
from typing import Optional, Dict, Any


# Gesture (Trigger.value) -> friendly line-1 label.
TRIGGER_LABELS = {
    "press": "Single Press",
    "double_press": "Double Press",
    "triple_press": "Triple Press",
    "long_press": "Long Press",
    "rotate_left": "Knob Left",
    "rotate_right": "Knob Right",
    "press_rotate_left": "Press + Knob Left",
    "press_rotate_right": "Press + Knob Right",
}

# Action name -> friendly line-2 label (for actions without parameters).
_ACTION_LABELS = {
    "volume_up": "Volume Up",
    "volume_down": "Volume Down",
    "mute": "Mute / Unmute",
    "mic_mute_toggle": "Mic Mute",
    "media_play_pause": "Play / Pause",
    "media_next": "Next Track",
    "media_prev": "Previous Track",
    "scroll_up": "Scroll Up",
    "scroll_down": "Scroll Down",
    "launch": "Launch",
    "run": "Run Command",
}

UNBOUND = "—"  # em dash


def _pretty_keys(combo: str) -> str:
    """Turn 'ctrl+right' into 'Ctrl+Right' for display."""
    parts = [p.strip() for p in str(combo).split("+") if p.strip()]
    return "+".join(p.capitalize() for p in parts)


def action_label(action_config: Optional[Dict[str, Any]]) -> str:
    """Friendly line-2 label for a bound action config."""
    if not action_config:
        return UNBOUND
    action = action_config.get("action", "none")
    if not action or action == "none":
        return UNBOUND
    if action == "key":
        keys = action_config.get("keys", "")
        return _pretty_keys(keys) if keys else "Key"
    if action == "macro":
        seq = action_config.get("sequence", []) or []
        if seq:
            return " › ".join(_pretty_keys(s) for s in seq)
        return "Macro"
    if action == "launch":
        path = action_config.get("path", "")
        return f"Launch: {path}" if path else "Launch"
    if action == "run":
        cmd = action_config.get("command", "")
        return f"Run: {cmd}" if cmd else "Run Command"
    return _ACTION_LABELS.get(action, action)


class OSD:
    """Borderless, translucent, always-on-top two-line overlay."""

    def __init__(self):
        self.root: Optional[tk.Misc] = None
        self.win: Optional[tk.Toplevel] = None
        self.frame: Optional[tk.Frame] = None
        self.label1: Optional[tk.Label] = None
        self.label2: Optional[tk.Label] = None

        # Options (live-updatable).
        self.enabled = True
        self.opacity = 0.85
        self.duration_ms = 1200
        self.bg_color = "#1a1a1a"
        self.font_family = "Segoe UI"
        self.font_color = "#ffffff"
        self.font_size = 15

        # Timers / state.
        self._hide_job = None
        self._fade_job = None

    def attach(self, root: tk.Misc):
        """Bind the OSD to the Tk root (called from the main thread)."""
        self.root = root

    def set_options(self, enabled=None, opacity=None, duration_ms=None,
                    bg_color=None, font_family=None, font_color=None,
                    font_size=None):
        """Apply option changes; live-update the widget if it exists."""
        if enabled is not None:
            self.enabled = bool(enabled)
        if opacity is not None:
            self.opacity = max(0.1, min(1.0, float(opacity)))
        if duration_ms is not None:
            self.duration_ms = max(200, int(duration_ms))
        if bg_color is not None:
            self.bg_color = str(bg_color)
        if font_family is not None:
            self.font_family = str(font_family)
        if font_color is not None:
            self.font_color = str(font_color)
        if font_size is not None:
            self.font_size = max(8, min(24, int(font_size)))

        if not self.enabled:
            self._withdraw()
        elif self.win is not None:
            self._restyle()

    # ----- thread-safe entry point -----
    def show(self, line1: str, line2: str):
        """Show the OSD (safe to call from any thread)."""
        if not self.enabled or self.root is None:
            return
        try:
            self.root.after(0, lambda: self._render(line1, line2))
        except Exception:
            pass

    # ----- main-thread internals -----
    def _ensure_window(self):
        if self.win is not None:
            return
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        try:
            self.win.wm_attributes("-topmost", True)
            self.win.wm_attributes("-toolwindow", True)
        except tk.TclError:
            pass
        self.win.withdraw()

        self.frame = tk.Frame(self.win, bg=self.bg_color)
        self.frame.pack(fill="both", expand=True)

        self.label1 = tk.Label(self.frame, bg=self.bg_color, fg=self.font_color,
                               anchor="w", justify="left")
        self.label1.pack(fill="x", padx=14, pady=(8, 0))
        self.label2 = tk.Label(self.frame, bg=self.bg_color, fg=self.font_color,
                               anchor="w", justify="left")
        self.label2.pack(fill="x", padx=14, pady=(0, 8))

        self._restyle()

    def _restyle(self):
        """Apply colors/fonts/geometry from current options."""
        if self.win is None:
            return
        size1 = self.font_size
        size2 = max(8, self.font_size - 2)
        self.frame.configure(bg=self.bg_color)
        self.label1.configure(bg=self.bg_color, fg=self.font_color,
                              font=(self.font_family, size1, "bold"))
        self.label2.configure(bg=self.bg_color, fg=self.font_color,
                              font=(self.font_family, size2, "normal"))
        try:
            self.win.wm_attributes("-alpha", self.opacity)
        except tk.TclError:
            pass
        self._reposition()

    def _reposition(self):
        """Place the overlay in the bottom-right of the work area (above the taskbar)."""
        if self.win is None:
            return
        # Size scales modestly with font size.
        w = 240 + self.font_size * 4
        h = 44 + self.font_size * 2
        right, bottom = self._work_area_br()
        x = right - w - 12
        y = bottom - h - 8  # bottom = top edge of the taskbar, so this sits above it
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _work_area_br(self):
        """(right, bottom) of the primary monitor's work area, excluding the taskbar.

        Falls back to the full screen size if the Win32 query is unavailable.
        """
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0,
                                                          ctypes.byref(rect), 0):
                return rect.right, rect.bottom
        except Exception:
            pass
        return self.win.winfo_screenwidth(), self.win.winfo_screenheight()

    def _render(self, line1: str, line2: str):
        if not self.enabled:
            return
        self._ensure_window()
        self._cancel_jobs()
        self.label1.configure(text=line1)
        self.label2.configure(text=line2)
        self._reposition()
        try:
            self.win.wm_attributes("-alpha", self.opacity)
        except tk.TclError:
            pass
        self.win.deiconify()
        self.win.lift()
        self._hide_job = self.root.after(self.duration_ms, self._begin_fade)

    def _begin_fade(self, step: int = 0):
        if self.win is None:
            return
        steps = 6
        if step >= steps:
            self._withdraw()
            return
        alpha = self.opacity * (1.0 - (step + 1) / steps)
        try:
            self.win.wm_attributes("-alpha", max(0.0, alpha))
        except tk.TclError:
            pass
        self._fade_job = self.root.after(30, lambda: self._begin_fade(step + 1))

    def _cancel_jobs(self):
        for job in (self._hide_job, self._fade_job):
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self._hide_job = None
        self._fade_job = None

    def _withdraw(self):
        self._cancel_jobs()
        if self.win is not None:
            try:
                self.win.withdraw()
            except tk.TclError:
                pass
