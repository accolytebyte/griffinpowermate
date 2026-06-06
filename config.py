"""Configuration management: load, save, validate config.json."""
import json
import logging
import threading
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "timing": {
        "multi_click_ms": 250,
        "long_press_ms": 500,
        "rotate_sensitivity": 1.0,
        "rotate_acceleration": 0.0
    },
    "led": {
        "mode": "volume",
        "brightness": 1.0,
        "pulse_speed": 255,
        "pulse_table": 0,
        "flash_on_ms": 200,
        "flash_off_ms": 800,
        "fade_speed": 1.0,
        "fade_delay": 1.0
    },
    "start_with_windows": False,
    "profiles": {
        "default": {
            "rotate_right": {"action": "volume_up", "amount": 0.04},
            "rotate_left": {"action": "volume_down", "amount": 0.04},
            "press": {"action": "mute"},
            "double_press": {"action": "media_play_pause"},
            "triple_press": {"action": "media_next"},
            "long_press": {"action": "mic_mute_toggle"},
            "press_rotate_right": {"action": "scroll_down", "amount": 3},
            "press_rotate_left": {"action": "scroll_up", "amount": 3}
        }
    }
}


class Config:
    """Configuration loader and manager."""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        # Reentrant: reload() holds the lock and may call save() (first run).
        self._lock = threading.RLock()
        self._callbacks = []
        self._last_mtime = 0

        # Load config (creates a default file on first run)
        self.reload()

        # Watch for file changes
        self._watch_thread = threading.Thread(target=self._watch_file, daemon=True)
        self._watch_thread.start()

    def reload(self):
        """Reload config from file, or create default if missing."""
        with self._lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        self.config = json.load(f)
                    logger.info(f"Loaded config from {self.config_file}")
                    self._last_mtime = os.path.getmtime(self.config_file)
                except Exception as e:
                    logger.error(f"Error loading config: {e}")
                    self.config = DEFAULT_CONFIG.copy()
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.save()

    def save(self):
        """Save current config to file."""
        with self._lock:
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                logger.info(f"Saved config to {self.config_file}")
                self._last_mtime = os.path.getmtime(self.config_file)
            except Exception as e:
                logger.error(f"Error saving config: {e}")

    def get(self, path: str, default: Any = None) -> Any:
        """Get value by dot-separated path (e.g. "timing.multi_click_ms")."""
        with self._lock:
            parts = path.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        return default
                else:
                    return default
            return value

    def set(self, path: str, value: Any):
        """Set value by dot-separated path."""
        with self._lock:
            parts = path.split(".")
            target = self.config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value

    def get_profile(self, process_name: Optional[str]) -> Dict[str, Any]:
        """Get effective bindings for a process.

        App-specific profiles inherit from 'default' for any trigger they
        don't explicitly override (a trigger set to {"action": "none"} counts
        as an explicit override).
        """
        with self._lock:
            profiles = self.config.get("profiles", {})
            default = profiles.get("default", {})
            if process_name and process_name in profiles and process_name != "default":
                merged = dict(default)
                merged.update(profiles[process_name])
                return merged
            return dict(default)

    def get_profile_raw(self, process_name: str) -> Dict[str, Any]:
        """Get a profile's own bindings without default inheritance (for editing)."""
        with self._lock:
            return dict(self.config.get("profiles", {}).get(process_name, {}))

    def add_profile(self, name: str):
        """Add a new profile (inherits from default)."""
        with self._lock:
            if "profiles" not in self.config:
                self.config["profiles"] = {}
            if name not in self.config["profiles"]:
                self.config["profiles"][name] = {}

    def delete_profile(self, name: str):
        """Delete a profile (except 'default')."""
        if name == "default":
            logger.warning("Cannot delete 'default' profile")
            return
        with self._lock:
            if "profiles" in self.config and name in self.config["profiles"]:
                del self.config["profiles"][name]

    def get_profiles(self) -> list:
        """Get list of profile names."""
        with self._lock:
            return list(self.config.get("profiles", {}).keys())

    def on_change(self, callback):
        """Register callback to be called when config changes."""
        self._callbacks.append(callback)

    def _watch_file(self):
        """Watch config file for external changes."""
        while True:
            try:
                if os.path.exists(self.config_file):
                    mtime = os.path.getmtime(self.config_file)
                    if mtime != self._last_mtime:
                        self.reload()
                        for callback in self._callbacks:
                            try:
                                callback()
                            except Exception as e:
                                logger.debug(f"Error in config change callback: {e}")
            except Exception as e:
                logger.debug(f"Error watching config file: {e}")

            import time
            time.sleep(1)
