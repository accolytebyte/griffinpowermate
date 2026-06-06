"""Main settings window using CustomTkinter."""
import customtkinter as ctk
from typing import Optional, Callable, Dict
from .profile_view import ProfileView
from .led_panel import LEDPanel
from .timing_panel import TimingPanel
from config import Config
from app_monitor import get_running_processes


SELECTED_COLOR = "#1f6aa5"


class AppWindow:
    """Main application settings window."""

    def __init__(self, config: Config, on_config_change: Callable = None):
        self.config = config
        self.on_config_change = on_config_change or (lambda: None)
        self.window: Optional[ctk.CTk] = None
        self.profile_view: Optional[ProfileView] = None
        self.led_panel: Optional[LEDPanel] = None
        self.timing_panel: Optional[TimingPanel] = None
        self.status_label: Optional[ctk.CTkLabel] = None

        self.sidebar: Optional[ctk.CTkScrollableFrame] = None
        self.profile_buttons: Dict[str, ctk.CTkButton] = {}
        self.selected_profile: Optional[str] = None
        self._status_text = ("Initializing...", "gray")

    def create(self):
        """Create and setup the main window."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.window = ctk.CTk()
        self.window.title("Griffin PowerMate Configuration")
        self.window.geometry("1000x600")

        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left sidebar: profile selector
        left_frame = ctk.CTkFrame(main_frame, width=200)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)

        ctk.CTkLabel(left_frame, text="Profiles", font=("Arial", 14, "bold")).pack(pady=(5, 10))

        self.sidebar = ctk.CTkScrollableFrame(left_frame, width=180)
        self.sidebar.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkButton(left_frame, text="+ Add Profile", command=self._add_profile).pack(fill="x", pady=(0, 5))
        ctk.CTkButton(left_frame, text="- Delete Profile", command=self._delete_profile,
                      fg_color="#8a3030", hover_color="#a33").pack(fill="x")

        # Right panel: tabs
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        self.notebook = ctk.CTkTabview(right_frame)
        self.notebook.pack(fill="both", expand=True)

        self.profile_view = ProfileView(self.notebook.add("Bindings"), self.config)
        self.profile_view.create()

        self.led_panel = LEDPanel(self.notebook.add("LED"), self.config, on_apply=self._apply_live)
        self.led_panel.create()

        self.timing_panel = TimingPanel(self.notebook.add("Timing"), self.config)
        self.timing_panel.create()

        # Status bar
        status_frame = ctk.CTkFrame(self.window)
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(status_frame, text="Status: Initializing...", text_color="gray")
        self.status_label.pack(side="left")

        ctk.CTkButton(status_frame, text="Save", command=self._save).pack(side="right", padx=(5, 0))
        ctk.CTkButton(status_frame, text="Reload", command=self._reload).pack(side="right", padx=(5, 0))

        self.window.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        self._refresh_profile_list()
        # Auto-select the default profile so the Bindings tab isn't empty.
        self._select_profile("default")
        self._apply_status()

        return self.window

    def show(self):
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus()

    def hide(self):
        if self.window:
            self.window.withdraw()

    def set_status(self, message: str, color: str = "gray"):
        """Thread-safe status update (may be called from worker threads)."""
        self._status_text = (message, color)
        if self.window:
            try:
                self.window.after(0, self._apply_status)
            except Exception:
                pass

    def _apply_status(self):
        if self.status_label:
            msg, color = self._status_text
            self.status_label.configure(text=f"Status: {msg}", text_color=color)

    def _refresh_profile_list(self):
        """Rebuild the sidebar profile buttons."""
        if not self.sidebar:
            return
        for btn in self.profile_buttons.values():
            btn.destroy()
        self.profile_buttons.clear()

        for profile in self.config.get_profiles():
            label = f"{profile}  (default)" if profile == "default" else profile
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                fg_color="transparent", hover_color="#333",
                command=lambda p=profile: self._select_profile(p),
            )
            btn.pack(fill="x", pady=2)
            self.profile_buttons[profile] = btn

        self._highlight_selected()

    def _highlight_selected(self):
        for profile, btn in self.profile_buttons.items():
            btn.configure(fg_color=SELECTED_COLOR if profile == self.selected_profile else "transparent")

    def _select_profile(self, name: str):
        self.selected_profile = name
        self._highlight_selected()
        if self.profile_view:
            self.profile_view.load_profile(name)

    def _add_profile(self):
        """Add a new profile by picking a running application."""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Add Profile")
        dialog.geometry("320x440")
        dialog.transient(self.window)
        dialog.after(100, dialog.grab_set)

        ctk.CTkLabel(dialog, text="Select an application:", font=("Arial", 12, "bold")).pack(pady=10)

        scroll = ctk.CTkScrollableFrame(dialog, width=290, height=340)
        scroll.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        existing = set(self.config.get_profiles())

        def pick(proc_name: str):
            self.config.add_profile(proc_name)
            self.config.save()
            self._refresh_profile_list()
            self._select_profile(proc_name)
            dialog.destroy()

        for proc in get_running_processes():
            if proc in existing:
                continue
            ctk.CTkButton(scroll, text=proc, anchor="w", fg_color="transparent",
                          hover_color="#333", command=lambda p=proc: pick(p)).pack(fill="x", pady=1)

    def _delete_profile(self):
        """Delete the currently selected profile (except 'default')."""
        name = self.selected_profile
        if not name or name == "default":
            self.set_status("Cannot delete the default profile", "orange")
            return
        self.config.delete_profile(name)
        self.config.save()
        self.selected_profile = "default"
        self._refresh_profile_list()
        self._select_profile("default")

    def _apply_live(self):
        """Apply unsaved LED panel changes to the running device immediately."""
        self.on_config_change()

    def _save(self):
        # Persist LED + timing into the in-memory config, then the current
        # profile's bindings, then flush to disk once.
        if self.led_panel:
            self.led_panel.save()
        if self.timing_panel:
            self.timing_panel.save()
        if self.profile_view:
            self.profile_view.save()
        self.config.save()
        self.set_status("Saved", "green")
        self.on_config_change()

    def _reload(self):
        self.config.reload()
        self._refresh_profile_list()
        if self.profile_view:
            self.profile_view.reload()
        if self.led_panel:
            self.led_panel.reload()
        if self.timing_panel:
            self.timing_panel.reload()
        self.set_status("Reloaded", "green")

    def _hide_to_tray(self):
        self.hide()
