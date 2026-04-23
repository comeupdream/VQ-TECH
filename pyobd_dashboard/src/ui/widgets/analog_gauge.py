import tkinter as tk
import customtkinter as ctk
import math
from ui.theme import ThemeManager

class AnalogGauge(ctk.CTkFrame):
    """Racing-style analog gauge with needle, markers, and tick marks."""

    def __init__(self, parent, width=180, height=180, min_val=0, max_val=100, unit="", danger_threshold=0.85):
        super().__init__(parent, width=width, height=height, fg_color="transparent")

        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.current_value = min_val
        self.danger_threshold = danger_threshold  # Red zone starts at this fraction

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=ThemeManager.get("GAUGE_BG"),
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill="both")

        self.size = width
        self.center_x = width / 2
        self.center_y = height / 2
        self.radius = width / 2 - 15

        # Arc angles (225° to -45°, sweeping 270°)
        self.start_angle = 225  # bottom-left
        self.end_angle = -45    # bottom-right
        self.sweep_range = 270

        # Create gauge elements
        self._create_gauge_elements()
        self.redraw_colors()
        self.update_value(self.min_val)

    def _create_gauge_elements(self):
        """Create all gauge visual elements."""
        # Background circle
        self.bg_circle = self.canvas.create_oval(
            self.center_x - self.radius,
            self.center_y - self.radius,
            self.center_x + self.radius,
            self.center_y + self.radius,
            fill=ThemeManager.get("GAUGE_BG"),
            outline=ThemeManager.get("ACCENT_DIM"),
            width=2
        )

        # Danger zone arc (red area at high values)
        self.danger_arc = self.canvas.create_arc(
            self.center_x - self.radius,
            self.center_y - self.radius,
            self.center_x + self.radius,
            self.center_y + self.radius,
            start=self.start_angle,
            extent=int(self.sweep_range * (1 - self.danger_threshold)),
            style="arc",
            width=8,
            outline=ThemeManager.get("WARNING")
        )

        # Create tick marks and labels
        self._create_ticks_and_labels()

        # Needle (line from center to edge)
        self.needle = self.canvas.create_line(
            self.center_x, self.center_y,
            self.center_x, self.center_y - self.radius + 10,
            fill=ThemeManager.get("ACCENT"),
            width=3
        )

        # Center circle (needle pivot point)
        pivot_size = 8
        self.center_circle = self.canvas.create_oval(
            self.center_x - pivot_size,
            self.center_y - pivot_size,
            self.center_x + pivot_size,
            self.center_y + pivot_size,
            fill=ThemeManager.get("ACCENT"),
            outline=ThemeManager.get("ACCENT")
        )

        # Value text (digital readout)
        self.text_val = self.canvas.create_text(
            self.center_x,
            self.center_y - 10,
            text="--",
            font=("Arial", 18, "bold"),
            fill=ThemeManager.get("ACCENT")
        )

        # Unit text
        self.text_unit = self.canvas.create_text(
            self.center_x,
            self.center_y + 15,
            text=self.unit,
            font=("Arial", 9),
            fill=ThemeManager.get("TEXT_DIM")
        )

    def _create_ticks_and_labels(self):
        """Create tick marks and numeric labels around gauge."""
        self.tick_marks = []
        self.tick_labels = []

        num_ticks = 11  # 0, 10, 20, ..., 100
        tick_interval = self.sweep_range / (num_ticks - 1)

        for i in range(num_ticks):
            angle_deg = self.start_angle - (i * tick_interval)
            angle_rad = math.radians(angle_deg)

            # Tick mark positions
            outer_r = self.radius - 5
            inner_r = self.radius - 15

            x1 = self.center_x + outer_r * math.cos(angle_rad)
            y1 = self.center_y + outer_r * math.sin(angle_rad)
            x2 = self.center_x + inner_r * math.cos(angle_rad)
            y2 = self.center_y + inner_r * math.sin(angle_rad)

            # Draw tick mark
            tick = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=ThemeManager.get("ACCENT_DIM"),
                width=2
            )
            self.tick_marks.append(tick)

            # Add numeric label
            label_r = self.radius - 25
            label_x = self.center_x + label_r * math.cos(angle_rad)
            label_y = self.center_y + label_r * math.sin(angle_rad)

            label_val = int(self.min_val + (i / (num_ticks - 1)) * (self.max_val - self.min_val))
            label = self.canvas.create_text(
                label_x, label_y,
                text=str(label_val),
                font=("Arial", 8),
                fill=ThemeManager.get("TEXT_DIM")
            )
            self.tick_labels.append(label)

    def redraw_colors(self):
        """Redraw gauge with current theme colors."""
        try:
            self.canvas.configure(bg=ThemeManager.get("GAUGE_BG"))
            self.canvas.itemconfigure(self.bg_circle, fill=ThemeManager.get("GAUGE_BG"), outline=ThemeManager.get("ACCENT_DIM"))
            self.canvas.itemconfigure(self.danger_arc, outline=ThemeManager.get("WARNING"))
            self.canvas.itemconfigure(self.needle, fill=ThemeManager.get("ACCENT"))
            self.canvas.itemconfigure(self.center_circle, fill=ThemeManager.get("ACCENT"), outline=ThemeManager.get("ACCENT"))

            for tick in self.tick_marks:
                self.canvas.itemconfigure(tick, fill=ThemeManager.get("ACCENT_DIM"))
            for label in self.tick_labels:
                self.canvas.itemconfigure(label, fill=ThemeManager.get("TEXT_DIM"))

            self.canvas.itemconfigure(self.text_unit, fill=ThemeManager.get("TEXT_DIM"))
            self.update_value(self.current_value)
        except Exception:
            pass

    def update_value(self, value):
        """Update gauge needle and value display."""
        try:
            self.current_value = value

            if self.max_val <= self.min_val:
                self.max_val = self.min_val + 1

            # Clamp value to range
            if value < self.min_val:
                value = self.min_val
            if value > self.max_val:
                value = self.max_val

            # Calculate needle angle (0 at bottom-left, sweeping clockwise)
            pct = (value - self.min_val) / (self.max_val - self.min_val)
            angle_deg = self.start_angle - (pct * self.sweep_range)
            angle_rad = math.radians(angle_deg)

            # Needle endpoint
            needle_r = self.radius - 10
            needle_x = self.center_x + needle_r * math.cos(angle_rad)
            needle_y = self.center_y + needle_r * math.sin(angle_rad)

            # Update needle color based on danger threshold
            needle_color = ThemeManager.get("ACCENT")
            text_color = ThemeManager.get("ACCENT")
            if pct >= self.danger_threshold:
                needle_color = ThemeManager.get("WARNING")
                text_color = ThemeManager.get("WARNING")

            self.canvas.coords(self.needle, self.center_x, self.center_y, needle_x, needle_y)
            self.canvas.itemconfigure(self.needle, fill=needle_color)

            # Update value text
            if isinstance(value, float) and abs(value) < 10:
                text_str = f"{value:.1f}"
            else:
                text_str = str(int(value))

            self.canvas.itemconfigure(self.text_val, text=text_str, fill=text_color)
        except Exception:
            pass