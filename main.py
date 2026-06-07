"""Main application: orchestration, worker threads, tray."""
import threading
import time
import logging
from typing import Optional
import customtkinter as ctk

from device import PowerMateDevice
from gesture import GestureDetector, GestureConfig, Trigger
from led import LEDController, LEDMode
from actions import ActionExecutor
from audio import AudioController
from app_monitor import get_active_process_name
from config import Config
from tray import TrayIcon
from ui.app_window import AppWindow
from ui.osd import OSD, TRIGGER_LABELS, action_label

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('powermate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PowerMateApp:
    """Main application controller."""

    def __init__(self):
        # Core components
        self.config = Config()
        self.device = PowerMateDevice()
        self.audio = AudioController()
        self.executor = ActionExecutor(self.audio, on_led_change=self._on_led_change)

        # Gesture detection
        gesture_config = GestureConfig(
            multi_click_ms=self.config.get("timing.multi_click_ms", 250),
            long_press_ms=self.config.get("timing.long_press_ms", 500)
        )
        self.gesture = GestureDetector(self._on_gesture, gesture_config)

        # LED control
        self.led = LEDController(self.device, self.audio.get_volume)
        self._setup_led_from_config()

        # UI
        self.app_window: Optional[AppWindow] = None
        self.tray: Optional[TrayIcon] = None
        self.osd = OSD()
        self._apply_osd_from_config()

        # Control
        self.running = False
        self.paused = False
        self.worker_thread: Optional[threading.Thread] = None

        # Config change callback
        self.config.on_change(self._on_config_change)

    def _setup_led_from_config(self):
        """Setup LED controller from config."""
        self.led.mode = LEDMode(self.config.get("led.mode", "volume"))
        self.led.brightness = self.config.get("led.brightness", 1.0)
        self.led.pulse_speed = self.config.get("led.pulse_speed", 255)
        self.led.pulse_table = self.config.get("led.pulse_table", 0)
        self.led.flash_on_ms = self.config.get("led.flash_on_ms", 200)
        self.led.flash_off_ms = self.config.get("led.flash_off_ms", 800)
        self.led.fade_speed = self.config.get("led.fade_speed", 1.0)
        self.led.fade_delay = self.config.get("led.fade_delay", 1.0)

    def _apply_osd_from_config(self):
        """Push OSD settings from config into the overlay."""
        self.osd.set_options(
            enabled=self.config.get("osd.enabled", True),
            opacity=self.config.get("osd.opacity", 0.85),
            duration_ms=self.config.get("osd.duration_ms", 1200),
            bg_color=self.config.get("osd.bg_color", "#1a1a1a"),
            font_family=self.config.get("osd.font_family", "Segoe UI"),
            font_color=self.config.get("osd.font_color", "#ffffff"),
            font_size=self.config.get("osd.font_size", 15),
        )

    def start(self):
        """Start the application."""
        logger.info("PowerMate app starting")
        self.running = True

        # Start LED controller
        self.led.start()

        # Start device worker thread
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

        # Start UI
        self._setup_ui()

        logger.info("PowerMate app started")

    def stop(self):
        """Stop the application."""
        logger.info("PowerMate app stopping")
        self.running = False

        if self.led:
            self.led.stop()

        if self.device.dev:
            self.device.close()

        if self.worker_thread:
            self.worker_thread.join(timeout=2)

        logger.info("PowerMate app stopped")

    def _setup_ui(self):
        """Setup GUI and tray."""
        # Tray icon
        self.tray = TrayIcon("assets/icon.ico")
        self.tray.on_show_settings = self._show_settings
        self.tray.on_pause = self._pause
        self.tray.on_resume = self._resume
        self.tray.on_quit = self._quit
        self.tray.start()

        # Main window
        self.app_window = AppWindow(self.config,
                                    on_config_change=self._on_config_change,
                                    on_quit=self._quit,
                                    on_osd_preview=self._preview_osd)
        root = self.app_window.create()
        self.osd.attach(root)

        # Run GUI loop
        try:
            root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def _preview_osd(self):
        """Flash a sample OSD using current settings (from the GUI Preview button)."""
        self.osd.show("Double Press", "Play / Pause")

    def _show_settings(self):
        """Show settings window."""
        if self.app_window:
            self.app_window.show()

    def _pause(self):
        """Pause knob processing."""
        self.paused = True
        logger.info("PowerMate paused")

    def _resume(self):
        """Resume knob processing."""
        self.paused = False
        logger.info("PowerMate resumed")

    def _quit(self):
        """Quit the application (invoked from the tray thread)."""
        self.stop()
        # Tk must be torn down on its own (main) thread.
        if self.app_window and self.app_window.window:
            try:
                self.app_window.window.after(0, self.app_window.window.quit)
            except Exception:
                pass

    def _on_led_change(self):
        """Called when LED should respond to an action."""
        self.led.on_volume_change()

    def _on_gesture(self, trigger: Trigger, amount: int):
        """Handle gesture event."""
        if self.paused:
            return

        logger.debug(f"Trigger: {trigger.value}, amount: {amount}")

        # Get active app
        app_name = get_active_process_name()
        logger.debug(f"Active app: {app_name}")

        # Get bindings for app (falls back to default)
        profile = self.config.get_profile(app_name)
        action_config = profile.get(trigger.value, {})
        action_name = action_config.get("action", "none") if action_config else "none"

        # Surface the event in the GUI debug panel.
        if self.app_window:
            amt = f" {amount:+d}" if amount else ""
            app_tag = f" [{app_name}]" if app_name else ""
            self.app_window.log_event(f"{trigger.value}{amt}{app_tag} -> {action_name}")

        # Translucent on-screen display of the gesture + bound action.
        self.osd.show(TRIGGER_LABELS.get(trigger.value, trigger.value),
                      action_label(action_config))

        if action_config:
            self.executor.execute(action_config, amount)

    def _on_config_change(self):
        """Called when config is reloaded."""
        logger.info("Config changed, reloading...")
        self._setup_led_from_config()
        self._apply_osd_from_config()

        # Update gesture timings
        self.gesture.config.multi_click_ms = self.config.get("timing.multi_click_ms", 250)
        self.gesture.config.long_press_ms = self.config.get("timing.long_press_ms", 500)

        if self.app_window:
            self.app_window.set_status("Config reloaded", "green")

    def _worker(self):
        """Worker thread: USB device communication."""
        search_interval = 5  # seconds
        last_connected = False

        while self.running:
            # Try to find and open device
            if not self.device.dev:
                if self.device.find():
                    last_connected = True
                    if self.app_window:
                        self.app_window.set_status("PowerMate connected", "green")
                    logger.info("PowerMate device connected")
                else:
                    if last_connected and self.app_window:
                        self.app_window.set_status("PowerMate not found", "red")
                    last_connected = False
                    time.sleep(search_interval)
                    continue

            # Read events
            try:
                def on_event(button: int, knob_delta: int):
                    self.gesture.on_button(button == 1)
                    self.gesture.on_knob(knob_delta)
                    self.gesture.update()

                self.device.read_events(on_event, timeout_ms=100)
            except Exception as e:
                logger.debug(f"Device read error: {e}")
                self.device.close()
                if self.app_window:
                    self.app_window.set_status("Device error", "red")

            # Update gesture state
            self.gesture.update()

            time.sleep(0.01)  # Small sleep to avoid busy loop


def main():
    """Entry point."""
    try:
        app = PowerMateApp()
        app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
