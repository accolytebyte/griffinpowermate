"""Profile bindings editor: trigger -> action mapping."""
import customtkinter as ctk
from typing import Dict, Any, Optional
from .action_editor import ActionEditor
from config import Config
from gesture import Trigger


class ProfileView:
    """Editor for profile trigger->action bindings."""

    TRIGGERS = [
        "rotate_right",
        "rotate_left",
        "press",
        "double_press",
        "triple_press",
        "long_press",
        "press_rotate_right",
        "press_rotate_left"
    ]

    def __init__(self, parent: ctk.CTkFrame, config: Config):
        self.parent = parent
        self.config = config
        self.current_profile: Optional[str] = None
        self.action_editors: Dict[str, ActionEditor] = {}
        self.frame: Optional[ctk.CTkFrame] = None

    def create(self):
        """Create the profile view."""
        self.frame = ctk.CTkScrollableFrame(self.parent)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Grid header
        ctk.CTkLabel(self.frame, text="Trigger", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ctk.CTkLabel(self.frame, text="Action", font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="w", pady=5, padx=10)
        ctk.CTkLabel(self.frame, text="Parameters", font=("Arial", 11, "bold")).grid(row=0, column=2, sticky="w", pady=5, padx=10)

        # Create action editors for each trigger
        for idx, trigger in enumerate(self.TRIGGERS, start=1):
            ctk.CTkLabel(self.frame, text=trigger, font=("Arial", 10)).grid(row=idx, column=0, sticky="w", pady=5)

            action_editor = ActionEditor(self.frame, trigger)
            action_editor.create()
            action_editor.grid(row=idx, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

            self.action_editors[trigger] = action_editor

    def load_profile(self, profile_name: str):
        """Load and display a profile's own bindings.

        Unset triggers show as 'none', which means "inherit from default" for
        app-specific profiles.
        """
        self.current_profile = profile_name
        profile = self.config.get_profile_raw(profile_name)

        for trigger, editor in self.action_editors.items():
            action_config = profile.get(trigger, {})
            editor.load(action_config)

    def reload(self):
        """Reload from config file."""
        if self.current_profile:
            self.load_profile(self.current_profile)

    def save(self):
        """Save current profile bindings."""
        if not self.current_profile:
            return

        bindings = {}
        for trigger, editor in self.action_editors.items():
            action = editor.get_action()
            # Only persist real overrides; 'none' triggers inherit from default.
            if action and action.get("action", "none") != "none":
                bindings[trigger] = action

        if "profiles" not in self.config.config:
            self.config.config["profiles"] = {}
        self.config.config["profiles"][self.current_profile] = bindings
        self.config.save()
