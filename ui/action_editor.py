"""Action editor widget for configuring trigger actions."""
import customtkinter as ctk
from typing import Dict, Any, Optional
import tkinter as tk


class ActionEditor(ctk.CTkFrame):
    """Widget to edit a single action configuration."""

    ACTIONS = [
        "none",
        "volume_up",
        "volume_down",
        "mute",
        "mic_mute_toggle",
        "media_play_pause",
        "media_next",
        "media_prev",
        "scroll_up",
        "scroll_down",
        "key",
        "launch",
        "run"
    ]

    def __init__(self, parent, trigger_name: str):
        super().__init__(parent)
        self.trigger_name = trigger_name
        self.current_action: Optional[str] = None

        # UI elements
        self.action_dropdown: Optional[ctk.CTkComboBox] = None
        self.param_frame: Optional[ctk.CTkFrame] = None
        self.param_widgets: Dict[str, Any] = {}

    def create(self):
        """Create the action editor widget."""
        # Action dropdown
        self.action_dropdown = ctk.CTkComboBox(
            self,
            values=self.ACTIONS,
            command=self._on_action_changed,
            width=150
        )
        self.action_dropdown.pack(side="left", padx=5)

        # Parameter frame (changes based on action)
        self.param_frame = ctk.CTkFrame(self)
        self.param_frame.pack(side="left", fill="x", expand=True, padx=5)

    def _on_action_changed(self, action: str):
        """Handle action selection change."""
        self.current_action = action
        self._refresh_params(action)

    def _refresh_params(self, action: str):
        """Refresh parameter widgets based on action type."""
        # Clear old widgets
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_widgets.clear()

        if action == "none":
            pass

        elif action in ["volume_up", "volume_down", "scroll_up", "scroll_down"]:
            ctk.CTkLabel(self.param_frame, text="Amount:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(self.param_frame, width=80)
            entry.pack(side="left", padx=2)
            entry.insert(0, "0.04" if action.startswith("volume") else "3")
            self.param_widgets["amount"] = entry

        elif action == "key":
            ctk.CTkLabel(self.param_frame, text="Keys:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(self.param_frame, width=150)
            entry.pack(side="left", padx=2)
            self.param_widgets["keys"] = entry

            # Record button
            ctk.CTkButton(
                self.param_frame,
                text="Record",
                command=self._record_keys,
                width=60
            ).pack(side="left", padx=2)

        elif action in ["launch"]:
            ctk.CTkLabel(self.param_frame, text="Path/URL:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(self.param_frame, width=200)
            entry.pack(side="left", padx=2)
            self.param_widgets["path"] = entry

        elif action == "run":
            ctk.CTkLabel(self.param_frame, text="Command:").pack(side="left", padx=5)
            entry = ctk.CTkEntry(self.param_frame, width=200)
            entry.pack(side="left", padx=2)
            self.param_widgets["command"] = entry

    # Tkinter keysym -> 'keyboard' library name normalisation
    _KEYSYM_MAP = {
        "Return": "enter", "Escape": "esc", "Prior": "page up",
        "Next": "page down", "BackSpace": "backspace", "Delete": "delete",
        "Up": "up", "Down": "down", "Left": "left", "Right": "right",
        "space": "space", "Tab": "tab", "Home": "home", "End": "end",
    }

    def _record_keys(self):
        """Open a modal that captures the next key combination."""
        if "keys" not in self.param_widgets:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Record Shortcut")
        dialog.geometry("320x120")
        dialog.transient(self.winfo_toplevel())
        ctk.CTkLabel(
            dialog,
            text="Press the key combination...\n(Esc to cancel)",
            font=("Arial", 12),
        ).pack(expand=True, fill="both", padx=10, pady=10)
        dialog.after(100, dialog.grab_set)

        def on_key(event):
            keysym = event.keysym
            # Ignore lone modifier presses; wait for a real key.
            if keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R",
                          "Alt_L", "Alt_R", "Win_L", "Win_R"):
                return
            if keysym == "Escape":
                dialog.destroy()
                return

            parts = []
            state = event.state
            if state & 0x0004:
                parts.append("ctrl")
            if state & 0x0001:
                parts.append("shift")
            if state & 0x20000 or state & 0x0008:  # Alt (Mod / Alt)
                parts.append("alt")

            key = self._KEYSYM_MAP.get(keysym, keysym.lower())
            parts.append(key)
            combo = "+".join(parts)

            self.param_widgets["keys"].delete(0, tk.END)
            self.param_widgets["keys"].insert(0, combo)
            dialog.destroy()

        dialog.bind("<KeyPress>", on_key)
        dialog.focus_force()

    def load(self, action_config: Dict[str, Any]):
        """Load an action configuration."""
        if not action_config or not action_config.get("action"):
            action = "none"
        else:
            action = action_config["action"]

        if self.action_dropdown:
            # set() does not fire the combobox command, so update state manually.
            self.current_action = action
            self.action_dropdown.set(action)
            self._refresh_params(action)

            # Load parameters
            for param_name, widget in self.param_widgets.items():
                if param_name in action_config:
                    value = action_config[param_name]
                    if isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, tk.END)
                        widget.insert(0, str(value))

    def get_action(self) -> Dict[str, Any]:
        """Get current action configuration."""
        if not self.current_action or self.current_action == "none":
            return {"action": "none"}

        config = {"action": self.current_action}

        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, ctk.CTkEntry):
                value = widget.get()
                try:
                    # Try to parse as number
                    config[param_name] = float(value) if "." in value else int(value)
                except ValueError:
                    config[param_name] = value

        return config
