"""LED configuration panel."""
import customtkinter as ctk
from typing import Optional
from config import Config


class LEDPanel(ctk.CTkFrame):
    """Panel for LED mode and effect configuration."""

    def __init__(self, parent, config: Config, on_apply=None):
        super().__init__(parent)
        self.config = config
        self.on_apply = on_apply or (lambda: None)
        self.widgets = {}

    def create(self):
        """Create the LED panel."""
        # Make this frame fill its tab (CTkFrame is not auto-packed).
        self.pack(fill="both", expand=True)

        # Mode selection
        frame_mode = ctk.CTkFrame(self)
        frame_mode.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_mode, text="LED Mode:", font=("Arial", 11, "bold")).pack(side="left", padx=5)
        mode_dropdown = ctk.CTkComboBox(
            frame_mode,
            values=["off", "solid", "pulse", "flash", "volume"],
            command=self._on_mode_changed
        )
        mode_dropdown.pack(side="left", padx=5)
        self.widgets["mode"] = mode_dropdown

        # Brightness (for solid mode)
        frame_brightness = ctk.CTkFrame(self)
        frame_brightness.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_brightness, text="Brightness:", font=("Arial", 11)).pack(side="left", padx=5)
        brightness_slider = ctk.CTkSlider(frame_brightness, from_=0, to=1, number_of_steps=100)
        brightness_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["brightness"] = brightness_slider

        # Pulse speed (for pulse mode)
        frame_pulse = ctk.CTkFrame(self)
        frame_pulse.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_pulse, text="Pulse Speed:", font=("Arial", 11)).pack(side="left", padx=5)
        pulse_slider = ctk.CTkSlider(frame_pulse, from_=0, to=510, number_of_steps=511)
        pulse_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["pulse_speed"] = pulse_slider

        pulse_label = ctk.CTkLabel(frame_pulse, text="255")
        pulse_label.pack(side="left", padx=5)
        self.widgets["pulse_speed_label"] = pulse_label

        pulse_slider.configure(command=lambda v: pulse_label.configure(text=str(int(float(v)))))

        # Pulse table (waveform)
        frame_table = ctk.CTkFrame(self)
        frame_table.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_table, text="Pulse Waveform:", font=("Arial", 11)).pack(side="left", padx=5)
        table_dropdown = ctk.CTkComboBox(frame_table, values=["0", "1", "2"])
        table_dropdown.pack(side="left", padx=5)
        self.widgets["pulse_table"] = table_dropdown

        # Flash timing
        frame_flash = ctk.CTkFrame(self)
        frame_flash.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_flash, text="Flash On (ms):", font=("Arial", 11)).pack(side="left", padx=5)
        flash_on = ctk.CTkEntry(frame_flash, width=80)
        flash_on.pack(side="left", padx=5)
        self.widgets["flash_on_ms"] = flash_on

        ctk.CTkLabel(frame_flash, text="Flash Off (ms):", font=("Arial", 11)).pack(side="left", padx=5)
        flash_off = ctk.CTkEntry(frame_flash, width=80)
        flash_off.pack(side="left", padx=5)
        self.widgets["flash_off_ms"] = flash_off

        # Volume tracking fade settings
        frame_fade = ctk.CTkFrame(self)
        frame_fade.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_fade, text="Fade Speed (s):", font=("Arial", 11)).pack(side="left", padx=5)
        fade_speed = ctk.CTkEntry(frame_fade, width=80)
        fade_speed.pack(side="left", padx=5)
        self.widgets["fade_speed"] = fade_speed

        ctk.CTkLabel(frame_fade, text="Fade Delay (s):", font=("Arial", 11)).pack(side="left", padx=5)
        fade_delay = ctk.CTkEntry(frame_fade, width=80)
        fade_delay.pack(side="left", padx=5)
        self.widgets["fade_delay"] = fade_delay

        # Test button
        ctk.CTkButton(self, text="Test LED", command=self._test_led).pack(padx=10, pady=10, fill="x")

        # Load initial values
        self.reload()

    def _on_mode_changed(self, mode: str):
        """Handle LED mode change."""
        pass

    def _test_led(self):
        """Apply the current panel settings to the live device."""
        self.save()
        self.on_apply()

    def reload(self):
        """Reload values from config."""
        self.widgets["mode"].set(self.config.get("led.mode", "volume"))
        self.widgets["brightness"].set(self.config.get("led.brightness", 1.0))
        self.widgets["pulse_speed"].set(self.config.get("led.pulse_speed", 255))
        self.widgets["pulse_table"].set(str(self.config.get("led.pulse_table", 0)))
        self.widgets["flash_on_ms"].delete(0, "end")
        self.widgets["flash_on_ms"].insert(0, str(self.config.get("led.flash_on_ms", 200)))
        self.widgets["flash_off_ms"].delete(0, "end")
        self.widgets["flash_off_ms"].insert(0, str(self.config.get("led.flash_off_ms", 800)))
        self.widgets["fade_speed"].delete(0, "end")
        self.widgets["fade_speed"].insert(0, str(self.config.get("led.fade_speed", 1.0)))
        self.widgets["fade_delay"].delete(0, "end")
        self.widgets["fade_delay"].insert(0, str(self.config.get("led.fade_delay", 1.0)))

    def save(self):
        """Save LED settings to config."""
        self.config.set("led.mode", self.widgets["mode"].get())
        self.config.set("led.brightness", self.widgets["brightness"].get())
        self.config.set("led.pulse_speed", int(float(self.widgets["pulse_speed"].get())))
        self.config.set("led.pulse_table", int(self.widgets["pulse_table"].get()))
        self.config.set("led.flash_on_ms", int(self.widgets["flash_on_ms"].get()))
        self.config.set("led.flash_off_ms", int(self.widgets["flash_off_ms"].get()))
        self.config.set("led.fade_speed", float(self.widgets["fade_speed"].get()))
        self.config.set("led.fade_delay", float(self.widgets["fade_delay"].get()))
