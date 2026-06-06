"""LED control modes: solid, pulse, flash, volume tracking."""
import threading
import time
import math
from enum import Enum
from typing import Optional, Callable
from device import PowerMateDevice

logger = __import__('logging').getLogger(__name__)


class LEDMode(Enum):
    """LED display modes."""
    OFF = "off"
    SOLID = "solid"
    PULSE = "pulse"
    FLASH = "flash"
    VOLUME = "volume"


class LEDController:
    """Manage LED behavior with background thread."""

    def __init__(self, device: PowerMateDevice, get_volume: Callable[[], float]):
        """
        device: PowerMateDevice instance
        get_volume: callable that returns current volume (0.0-1.0)
        """
        self.device = device
        self.get_volume = get_volume
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Configuration
        self.mode = LEDMode.VOLUME
        self.brightness = 1.0  # for SOLID mode
        self.pulse_speed = 255  # 0-510
        self.pulse_table = 0    # waveform table
        self.flash_on_ms = 200
        self.flash_off_ms = 800
        self.fade_speed = 1.0   # seconds to completely fade
        self.fade_delay = 1.0   # seconds before fade starts

        # Volume tracking state
        self._current_brightness = 1.0
        self._fade_time = 0.0
        self._volume_change_time = 0.0

        # Lock for thread safety
        self._lock = threading.Lock()

    def start(self):
        """Start the LED controller thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("LED controller started")

    def stop(self):
        """Stop the LED controller thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("LED controller stopped")

    def on_volume_change(self):
        """Call when volume changes (to trigger volume-track LED response)."""
        with self._lock:
            self._volume_change_time = time.time()

    def set_mode(self, mode: LEDMode):
        """Change LED mode."""
        with self._lock:
            self.mode = mode
            if mode == LEDMode.PULSE:
                # Enable hardware pulse
                self.device.set_pulse_mode(self.pulse_table, self.pulse_speed)
                self.device.set_pulse_awake(True)

    def _run(self):
        """Main LED controller loop."""
        prev_mode = None

        while self.running:
            with self._lock:
                mode = self.mode
                brightness = self.brightness
                fade_speed = self.fade_speed
                fade_delay = self.fade_delay
                pulse_speed = self.pulse_speed
                pulse_table = self.pulse_table

            now = time.time()
            mode_changed = mode != prev_mode

            # Leaving pulse mode: disable hardware pulse so static writes take effect.
            if prev_mode == LEDMode.PULSE and mode != LEDMode.PULSE:
                self.device.set_pulse_awake(False)
            prev_mode = mode

            if mode == LEDMode.OFF:
                self.device.set_brightness(0.0)

            elif mode == LEDMode.SOLID:
                self.device.set_brightness(brightness)

            elif mode == LEDMode.PULSE:
                # Software pulse (smooth sine). Hardware pulse uses vendor control
                # transfers that break the read pipe on WinUSB, so we drive the
                # brightness ourselves. pulse_speed (0-510) maps to a period.
                period = max(0.25, 3.0 - (pulse_speed / 510.0) * 2.75)
                phase = (now % period) / period
                level = 0.5 - 0.5 * math.cos(2 * math.pi * phase)
                self.device.set_brightness(level)

            elif mode == LEDMode.FLASH:
                # Software flash
                elapsed = (now * 1000) % (self.flash_on_ms + self.flash_off_ms)
                if elapsed < self.flash_on_ms:
                    self.device.set_brightness(1.0)
                else:
                    self.device.set_brightness(0.0)

            elif mode == LEDMode.VOLUME:
                # Volume tracking: LED = volume, then fade after delay
                volume = self.get_volume()
                time_since_change = now - self._volume_change_time

                if time_since_change < fade_delay:
                    # Volume just changed, show it
                    self._current_brightness = volume
                else:
                    # Fade down
                    fade_progress = (time_since_change - fade_delay) / fade_speed
                    if fade_progress > 1.0:
                        fade_progress = 1.0
                    self._current_brightness = volume * (1.0 - fade_progress)

                self.device.set_brightness(self._current_brightness)

            # Update every ~50ms
            time.sleep(0.05)
