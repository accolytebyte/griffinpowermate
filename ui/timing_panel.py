"""Timing configuration panel."""
import customtkinter as ctk
from config import Config


class TimingPanel(ctk.CTkFrame):
    """Panel for gesture timing configuration."""

    def __init__(self, parent, config: Config):
        super().__init__(parent)
        self.config = config
        self.widgets = {}

    def create(self):
        """Create the timing panel."""
        # Make this frame fill its tab (CTkFrame is not auto-packed).
        self.pack(fill="both", expand=True)

        # Multi-click window
        frame1 = ctk.CTkFrame(self)
        frame1.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame1, text="Multi-Click Window (ms):", font=("Arial", 11)).pack(side="left", padx=5)
        multi_click = ctk.CTkEntry(frame1, width=100)
        multi_click.pack(side="left", padx=5)
        self.widgets["multi_click_ms"] = multi_click

        info1 = ctk.CTkLabel(frame1, text="Time to detect double/triple press", text_color="gray", font=("Arial", 9))
        info1.pack(side="left", padx=5)

        # Long press threshold
        frame2 = ctk.CTkFrame(self)
        frame2.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame2, text="Long Press Threshold (ms):", font=("Arial", 11)).pack(side="left", padx=5)
        long_press = ctk.CTkEntry(frame2, width=100)
        long_press.pack(side="left", padx=5)
        self.widgets["long_press_ms"] = long_press

        info2 = ctk.CTkLabel(frame2, text="Time button must be held to trigger long_press", text_color="gray", font=("Arial", 9))
        info2.pack(side="left", padx=5)

        # Rotate sensitivity
        frame3 = ctk.CTkFrame(self)
        frame3.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame3, text="Rotation Sensitivity:", font=("Arial", 11)).pack(side="left", padx=5)
        rotate_sens = ctk.CTkSlider(frame3, from_=0.1, to=5.0, number_of_steps=49)
        rotate_sens.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["rotate_sensitivity"] = rotate_sens

        sens_label = ctk.CTkLabel(frame3, text="1.0", width=30)
        sens_label.pack(side="left", padx=5)

        rotate_sens.configure(command=lambda v: sens_label.configure(text=f"{float(v):.1f}"))

        # Rotate acceleration
        frame4 = ctk.CTkFrame(self)
        frame4.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame4, text="Rotation Acceleration:", font=("Arial", 11)).pack(side="left", padx=5)
        rotate_accel = ctk.CTkSlider(frame4, from_=0.0, to=1.0, number_of_steps=100)
        rotate_accel.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["rotate_acceleration"] = rotate_accel

        accel_label = ctk.CTkLabel(frame4, text="0.0", width=30)
        accel_label.pack(side="left", padx=5)

        rotate_accel.configure(command=lambda v: accel_label.configure(text=f"{float(v):.1f}"))

        # Load initial values
        self.reload()

    def reload(self):
        """Reload values from config."""
        self.widgets["multi_click_ms"].delete(0, "end")
        self.widgets["multi_click_ms"].insert(0, str(self.config.get("timing.multi_click_ms", 250)))

        self.widgets["long_press_ms"].delete(0, "end")
        self.widgets["long_press_ms"].insert(0, str(self.config.get("timing.long_press_ms", 500)))

        self.widgets["rotate_sensitivity"].set(self.config.get("timing.rotate_sensitivity", 1.0))
        self.widgets["rotate_acceleration"].set(self.config.get("timing.rotate_acceleration", 0.0))

    def save(self):
        """Save timing settings to config."""
        self.config.set("timing.multi_click_ms", int(self.widgets["multi_click_ms"].get()))
        self.config.set("timing.long_press_ms", int(self.widgets["long_press_ms"].get()))
        self.config.set("timing.rotate_sensitivity", float(self.widgets["rotate_sensitivity"].get()))
        self.config.set("timing.rotate_acceleration", float(self.widgets["rotate_acceleration"].get()))
