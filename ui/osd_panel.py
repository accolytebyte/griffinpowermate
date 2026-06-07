"""On-screen display (OSD) configuration panel."""
import tkinter as tk
from tkinter import colorchooser, font as tkfont
import customtkinter as ctk
from typing import Optional
from config import Config


class OSDPanel(ctk.CTkFrame):
    """Panel for the translucent OSD overlay settings."""

    def __init__(self, parent, config: Config, on_apply=None, on_preview=None):
        super().__init__(parent)
        self.config = config
        self.on_apply = on_apply or (lambda: None)
        self.on_preview = on_preview or (lambda: None)
        self.widgets = {}

    def create(self):
        # CTkFrame must pack itself to fill its tab.
        self.pack(fill="both", expand=True)

        # Enable toggle
        frame_enable = ctk.CTkFrame(self)
        frame_enable.pack(fill="x", padx=10, pady=(10, 5))
        self.widgets["enabled"] = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame_enable, text="Enable On-Screen Display",
                        variable=self.widgets["enabled"]).pack(side="left", padx=5)

        # Opacity
        frame_op = ctk.CTkFrame(self)
        frame_op.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_op, text="Opacity:", font=("Arial", 11)).pack(side="left", padx=5)
        op_slider = ctk.CTkSlider(frame_op, from_=0.2, to=1.0, number_of_steps=80)
        op_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["opacity"] = op_slider
        op_label = ctk.CTkLabel(frame_op, text="0.85", width=40)
        op_label.pack(side="left", padx=5)
        self.widgets["opacity_label"] = op_label
        op_slider.configure(command=lambda v: op_label.configure(text=f"{float(v):.2f}"))

        # Duration
        frame_dur = ctk.CTkFrame(self)
        frame_dur.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_dur, text="Duration (ms):", font=("Arial", 11)).pack(side="left", padx=5)
        dur_entry = ctk.CTkEntry(frame_dur, width=80)
        dur_entry.pack(side="left", padx=5)
        self.widgets["duration_ms"] = dur_entry

        # Background color
        frame_bg = ctk.CTkFrame(self)
        frame_bg.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_bg, text="Background:", font=("Arial", 11)).pack(side="left", padx=5)
        bg_entry = ctk.CTkEntry(frame_bg, width=100)
        bg_entry.pack(side="left", padx=5)
        self.widgets["bg_color"] = bg_entry
        bg_swatch = tk.Label(frame_bg, text="   ", bg="#1a1a1a", relief="solid", bd=1)
        bg_swatch.pack(side="left", padx=5)
        self.widgets["bg_swatch"] = bg_swatch
        ctk.CTkButton(frame_bg, text="Pick…", width=60,
                      command=lambda: self._pick_color(bg_entry, bg_swatch)).pack(side="left", padx=2)
        bg_entry.bind("<KeyRelease>", lambda e: self._sync_swatch(bg_entry, bg_swatch))

        # Font family
        frame_ff = ctk.CTkFrame(self)
        frame_ff.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_ff, text="Font:", font=("Arial", 11)).pack(side="left", padx=5)
        families = sorted(set(f for f in tkfont.families() if not f.startswith("@")))
        ff_combo = ctk.CTkComboBox(frame_ff, values=families, width=200)
        ff_combo.pack(side="left", padx=5)
        self.widgets["font_family"] = ff_combo

        # Font color
        frame_fc = ctk.CTkFrame(self)
        frame_fc.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_fc, text="Font color:", font=("Arial", 11)).pack(side="left", padx=5)
        fc_entry = ctk.CTkEntry(frame_fc, width=100)
        fc_entry.pack(side="left", padx=5)
        self.widgets["font_color"] = fc_entry
        fc_swatch = tk.Label(frame_fc, text="   ", bg="#ffffff", relief="solid", bd=1)
        fc_swatch.pack(side="left", padx=5)
        self.widgets["fc_swatch"] = fc_swatch
        ctk.CTkButton(frame_fc, text="Pick…", width=60,
                      command=lambda: self._pick_color(fc_entry, fc_swatch)).pack(side="left", padx=2)
        fc_entry.bind("<KeyRelease>", lambda e: self._sync_swatch(fc_entry, fc_swatch))

        # Font size
        frame_fs = ctk.CTkFrame(self)
        frame_fs.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_fs, text="Font size:", font=("Arial", 11)).pack(side="left", padx=5)
        fs_slider = ctk.CTkSlider(frame_fs, from_=8, to=24, number_of_steps=16)
        fs_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.widgets["font_size"] = fs_slider
        fs_label = ctk.CTkLabel(frame_fs, text="15", width=40)
        fs_label.pack(side="left", padx=5)
        self.widgets["font_size_label"] = fs_label
        fs_slider.configure(command=lambda v: fs_label.configure(text=str(int(float(v)))))

        # Preview
        ctk.CTkButton(self, text="Preview", command=self._preview).pack(padx=10, pady=10, fill="x")

        self.reload()

    def _pick_color(self, entry, swatch):
        initial = entry.get().strip() or "#1a1a1a"
        try:
            rgb, hexval = colorchooser.askcolor(color=initial, parent=self)
        except tk.TclError:
            rgb, hexval = colorchooser.askcolor(parent=self)
        if hexval:
            entry.delete(0, "end")
            entry.insert(0, hexval)
            self._sync_swatch(entry, swatch)

    def _sync_swatch(self, entry, swatch):
        val = entry.get().strip()
        try:
            swatch.configure(bg=val)
        except tk.TclError:
            pass

    def _preview(self):
        """Apply current settings live, then flash a sample OSD."""
        self.save()
        self.on_apply()
        self.on_preview()

    def reload(self):
        self.widgets["enabled"].set(bool(self.config.get("osd.enabled", True)))
        op = float(self.config.get("osd.opacity", 0.85))
        self.widgets["opacity"].set(op)
        self.widgets["opacity_label"].configure(text=f"{op:.2f}")
        self.widgets["duration_ms"].delete(0, "end")
        self.widgets["duration_ms"].insert(0, str(self.config.get("osd.duration_ms", 1200)))
        bg = self.config.get("osd.bg_color", "#1a1a1a")
        self.widgets["bg_color"].delete(0, "end")
        self.widgets["bg_color"].insert(0, bg)
        self._sync_swatch(self.widgets["bg_color"], self.widgets["bg_swatch"])
        self.widgets["font_family"].set(self.config.get("osd.font_family", "Segoe UI"))
        fc = self.config.get("osd.font_color", "#ffffff")
        self.widgets["font_color"].delete(0, "end")
        self.widgets["font_color"].insert(0, fc)
        self._sync_swatch(self.widgets["font_color"], self.widgets["fc_swatch"])
        fs = int(self.config.get("osd.font_size", 15))
        self.widgets["font_size"].set(fs)
        self.widgets["font_size_label"].configure(text=str(fs))

    def save(self):
        self.config.set("osd.enabled", bool(self.widgets["enabled"].get()))
        self.config.set("osd.opacity", round(float(self.widgets["opacity"].get()), 2))
        try:
            self.config.set("osd.duration_ms", max(200, int(float(self.widgets["duration_ms"].get()))))
        except ValueError:
            self.config.set("osd.duration_ms", 1200)
        self.config.set("osd.bg_color", self.widgets["bg_color"].get().strip() or "#1a1a1a")
        self.config.set("osd.font_family", self.widgets["font_family"].get())
        self.config.set("osd.font_color", self.widgets["font_color"].get().strip() or "#ffffff")
        self.config.set("osd.font_size", max(8, min(24, int(float(self.widgets["font_size"].get())))))
