"""System tray icon management."""
import os
import sys
import threading
from typing import Callable, Optional
from pystray import Icon, Menu, MenuItem
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def resource_path(rel: str) -> str:
    """Resolve a bundled resource path, working both from source and inside a
    PyInstaller one-file bundle (which extracts data to sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)


class TrayIcon:
    """Manages system tray icon and menu."""

    def __init__(self, icon_path: str = "assets/icon.ico"):
        self.icon_path = icon_path
        self.icon: Optional[Icon] = None
        self.thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_show_settings: Callable = lambda: None
        self.on_pause: Callable = lambda: None
        self.on_resume: Callable = lambda: None
        self.on_quit: Callable = lambda: None

        self.is_paused = False

    def start(self):
        """Start the tray icon in a background thread."""
        if self.thread:
            return

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Tray icon started")

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Tray icon stopped")

    def set_status(self, status: str, tooltip: str = "PowerMate"):
        """Update tray icon status/tooltip."""
        if self.icon:
            self.icon.tooltip = tooltip

    def _run(self):
        """Run the tray icon event loop."""
        try:
            # Load icon image (resolve for both source and frozen bundle).
            path = self.icon_path
            if not os.path.exists(path):
                path = resource_path(self.icon_path)
            image = Image.open(path)
        except Exception as e:
            logger.warning(f"Could not load icon {self.icon_path}: {e}")
            # Create a simple placeholder image
            image = Image.new('RGB', (64, 64), color='blue')

        # Create menu. The pause/resume label is a callable so it stays in sync
        # whenever update_menu() is called.
        menu = Menu(
            MenuItem("Settings", self._on_show_settings, default=True),
            MenuItem(lambda item: "Resume" if self.is_paused else "Pause",
                     self._on_pause_resume),
            MenuItem("Exit", self._on_quit)
        )

        # Create icon
        self.icon = Icon("PowerMate", image, menu=menu, title="PowerMate")

        try:
            self.icon.run()
        except Exception as e:
            logger.error(f"Tray icon error: {e}")

    def _on_show_settings(self, icon=None, item=None):
        """Handle Settings click."""
        self.on_show_settings()

    def _on_pause_resume(self, icon=None, item=None):
        """Handle Pause/Resume click."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.on_pause()
        else:
            self.on_resume()

        # Refresh the (callable) menu label.
        if self.icon:
            self.icon.update_menu()

    def _on_quit(self, icon=None, item=None):
        """Handle Quit click."""
        self.on_quit()
