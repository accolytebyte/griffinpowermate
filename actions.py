"""Action executors: what happens when a trigger fires."""
import logging
import subprocess
import os
import time
from typing import Callable, Any, Dict
from audio import AudioController
import pyautogui
import keyboard

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Execute actions triggered by PowerMate events."""

    def __init__(self, audio: AudioController, on_led_change: Callable = None):
        self.audio = audio
        self.on_led_change = on_led_change or (lambda: None)

    def execute(self, action_config: Dict[str, Any], amount: int = 0):
        """
        Execute an action based on configuration.
        action_config: {"action": "...", <other params>}
        amount: rotation delta (for scroll/volume actions)
        """
        if not action_config:
            return

        action = action_config.get("action", "none")

        try:
            if action == "none":
                pass

            elif action == "volume_up":
                self._volume_up((amount or 1) * action_config.get("amount", 0.04))

            elif action == "volume_down":
                self._volume_down((amount or 1) * action_config.get("amount", 0.04))

            elif action == "mute":
                self._mute_toggle()

            elif action == "mic_mute_toggle":
                self._mic_mute_toggle()

            elif action == "media_play_pause":
                self._media_key("play/pause media")

            elif action == "media_next":
                self._media_key("next track")

            elif action == "media_prev":
                self._media_key("previous track")

            elif action == "scroll_up":
                self._scroll((amount or 1) * action_config.get("amount", 3), direction="up")

            elif action == "scroll_down":
                self._scroll((amount or 1) * action_config.get("amount", 3), direction="down")

            elif action == "key":
                keys = action_config.get("keys", "")
                self._send_keys(keys)

            elif action == "macro":
                self._macro(action_config.get("sequence", []))

            elif action == "launch":
                path = action_config.get("path", "")
                self._launch(path)

            elif action == "run":
                cmd = action_config.get("command", "")
                self._run_command(cmd)

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")

    def _volume_up(self, amount: float):
        """Increase volume."""
        vol = self.audio.get_volume()
        self.audio.set_volume(vol + amount)
        self.on_led_change()

    def _volume_down(self, amount: float):
        """Decrease volume."""
        vol = self.audio.get_volume()
        self.audio.set_volume(vol - amount)
        self.on_led_change()

    def _mute_toggle(self):
        """Toggle mute."""
        self.audio.toggle_mute()
        self.on_led_change()

    def _mic_mute_toggle(self):
        """Toggle microphone mute."""
        self.audio.toggle_mic_mute()

    def _media_key(self, key: str):
        """Send media key (play pause, next, previous)."""
        try:
            keyboard.send(key)
        except Exception as e:
            logger.debug(f"Error sending media key {key}: {e}")

    def _scroll(self, amount: int, direction: str):
        """Scroll up or down."""
        # pyautogui.scroll() is positive for up, negative for down
        scroll_amount = amount if direction == "up" else -amount
        try:
            pyautogui.scroll(scroll_amount)
        except Exception as e:
            logger.debug(f"Error scrolling: {e}")

    def _send_keys(self, keys: str):
        """Send keyboard shortcut."""
        if not keys:
            return
        try:
            keyboard.send(keys)
        except Exception as e:
            logger.debug(f"Error sending keys '{keys}': {e}")

    def _macro(self, sequence):
        """Send a sequence of key combos in order (a keyboard macro)."""
        if not sequence:
            return
        for combo in sequence:
            combo = (combo or "").strip()
            if not combo:
                continue
            self._send_keys(combo)
            time.sleep(0.05)

    def _launch(self, path: str):
        """Launch file/application/URL."""
        if not path:
            return
        try:
            os.startfile(path)
        except Exception as e:
            logger.debug(f"Error launching {path}: {e}")

    def _run_command(self, command: str):
        """Run shell command."""
        if not command:
            return
        try:
            subprocess.Popen(command, shell=True)
        except Exception as e:
            logger.debug(f"Error running command '{command}': {e}")
