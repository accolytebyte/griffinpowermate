"""State machine for detecting multi-click, long-press, and press+rotate gestures."""
import time
from enum import Enum
from typing import Callable, Optional
from dataclasses import dataclass

class Trigger(Enum):
    """All possible trigger events."""
    ROTATE_RIGHT = "rotate_right"
    ROTATE_LEFT = "rotate_left"
    PRESS = "press"
    DOUBLE_PRESS = "double_press"
    TRIPLE_PRESS = "triple_press"
    LONG_PRESS = "long_press"
    PRESS_ROTATE_RIGHT = "press_rotate_right"
    PRESS_ROTATE_LEFT = "press_rotate_left"


@dataclass
class GestureConfig:
    """Configuration for gesture detection."""
    multi_click_ms: int = 250        # Window to detect double/triple click
    long_press_ms: int = 500         # Time to fire long_press
    rotate_sensitivity: float = 1.0  # Rotation accumulation threshold
    rotate_acceleration: float = 0.0 # Faster rotation gives more delta


class GestureDetector:
    """Detects gestures from raw button/knob events."""

    def __init__(self, callback: Callable[[Trigger, int], None], config: GestureConfig = None):
        """
        callback(trigger: Trigger, amount: int)
          - amount is the knob delta for rotations, 0 for clicks
        """
        self.callback = callback
        self.config = config or GestureConfig()

        # Button state machine
        self.button_pressed = False
        self.button_press_count = 0
        self.button_press_time = 0.0
        self.long_press_fired = False
        self.multi_click_active = False

        # Rotation state
        self.accumulated_rotation = 0.0
        self.pressed_and_rotating = False

    def on_button(self, pressed: bool):
        """Handle button down/up event."""
        now = time.time()

        if pressed:
            if not self.button_pressed:
                # Button just pressed
                self.button_pressed = True
                self.button_press_time = now
                self.long_press_fired = False
                self.pressed_and_rotating = False
                self.accumulated_rotation = 0.0
                self.button_press_count += 1
                self.multi_click_active = True
        else:
            if self.button_pressed:
                # Button just released
                self.button_pressed = False

                if self.pressed_and_rotating:
                    # We rotated while pressed: this was a press+rotate gesture,
                    # so cancel any pending click detection for this press.
                    self.pressed_and_rotating = False
                    self.accumulated_rotation = 0.0
                    self.multi_click_active = False
                    self.button_press_count = 0
                elif self.long_press_fired:
                    # Long press already handled on this press; don't let the
                    # release start/continue a multi-click sequence.
                    self.multi_click_active = False
                    self.button_press_count = 0
                # else: normal click, wait for multi-click window in update()

    def on_knob(self, delta: int):
        """Handle knob rotation delta."""
        # Accumulate rotation
        self.accumulated_rotation += delta * self.config.rotate_sensitivity

        threshold = 1.0
        if self.accumulated_rotation >= threshold:
            amount = int(self.accumulated_rotation)
            self.accumulated_rotation -= amount
            self._fire_rotation(amount)

        elif self.accumulated_rotation <= -threshold:
            amount = int(abs(self.accumulated_rotation))
            self.accumulated_rotation += amount
            self._fire_rotation(-amount)

    def _fire_rotation(self, amount: int):
        """Fire a rotation event."""
        if self.button_pressed:
            # Button is held, this is press+rotate
            self.pressed_and_rotating = True
            if amount > 0:
                self.callback(Trigger.PRESS_ROTATE_RIGHT, amount)
            else:
                self.callback(Trigger.PRESS_ROTATE_LEFT, abs(amount))
        else:
            # No button, just rotation
            if amount > 0:
                self.callback(Trigger.ROTATE_RIGHT, amount)
            else:
                self.callback(Trigger.ROTATE_LEFT, abs(amount))

    def update(self):
        """
        Call this periodically (~100ms) to detect long-press and multi-click timeout.
        Typically called from the main event loop.
        """
        now = time.time()

        # Detect long press (but not if the user is rotating while holding)
        if self.button_pressed and not self.long_press_fired and not self.pressed_and_rotating:
            elapsed = (now - self.button_press_time) * 1000
            if elapsed >= self.config.long_press_ms:
                self.long_press_fired = True
                self.button_press_count = 0  # Reset so multi-click doesn't fire after long press
                self.callback(Trigger.LONG_PRESS, 0)

        # Detect multi-click timeout
        if self.multi_click_active and not self.button_pressed:
            elapsed = (now - self.button_press_time) * 1000
            if elapsed >= self.config.multi_click_ms:
                self.multi_click_active = False

                if self.button_press_count == 1:
                    if not self.long_press_fired:
                        self.callback(Trigger.PRESS, 0)
                elif self.button_press_count == 2:
                    self.callback(Trigger.DOUBLE_PRESS, 0)
                elif self.button_press_count >= 3:
                    self.callback(Trigger.TRIPLE_PRESS, 0)

                self.button_press_count = 0
