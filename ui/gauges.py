"""Circular-arc gauge widgets using Dear PyGui drawlist primitives."""
import math
from typing import Optional

import dearpygui.dearpygui as dpg

from config.theme import ACCENT, ACCENT_2, DANGER, MUTED, TEXT, WARN


class Gauge:
    """Single arc gauge: sweep from -135° to +135° around a center point."""

    SIZE = 190
    RADIUS = 75
    START_DEG = -135
    END_DEG = 135

    def __init__(self, key: str, label: str,
                 vmin: float, vmax: float, danger_above: float, unit: str):
        self.key = key
        self.label = label
        self.vmin = vmin
        self.vmax = vmax
        self.danger_above = danger_above
        self.unit = unit
        self._value: Optional[float] = None
        self._draw_tag = dpg.generate_uuid()
        self._val_tag = dpg.generate_uuid()

    def build(self):
        with dpg.child_window(width=self.SIZE + 10,
                              height=self.SIZE + 10, border=True):
            dpg.add_text(self.label, color=MUTED)
            dpg.add_drawlist(width=self.SIZE, height=self.SIZE,
                             tag=self._draw_tag)
            dpg.add_text("--", tag=self._val_tag, color=TEXT)
        self._draw_static()

    def _draw_static(self):
        cx = cy = self.SIZE // 2
        steps = 48
        for i in range(steps):
            a0 = math.radians(self.START_DEG +
                              (self.END_DEG - self.START_DEG) * i / steps)
            a1 = math.radians(self.START_DEG +
                              (self.END_DEG - self.START_DEG) * (i + 1) / steps)
            p0 = (cx + self.RADIUS * math.cos(a0),
                  cy + self.RADIUS * math.sin(a0))
            p1 = (cx + self.RADIUS * math.cos(a1),
                  cy + self.RADIUS * math.sin(a1))
            dpg.draw_line(p0, p1, color=(*MUTED, 120), thickness=2,
                          parent=self._draw_tag)

    def update(self, value: Optional[float]):
        self._value = value
        dpg.delete_item(self._draw_tag, children_only=True, slot=2)
        self._draw_static()
        if value is None:
            dpg.set_value(self._val_tag, "--")
            return
        clamped = max(self.vmin, min(self.vmax, value))
        frac = (clamped - self.vmin) / (self.vmax - self.vmin)
        cx = cy = self.SIZE // 2
        color = ACCENT
        if value >= self.danger_above:
            color = DANGER
        elif value >= self.danger_above - (self.vmax - self.vmin) * 0.15:
            color = WARN
        steps = max(1, int(48 * frac))
        for i in range(steps):
            a0 = math.radians(self.START_DEG +
                              (self.END_DEG - self.START_DEG) * i / 48)
            a1 = math.radians(self.START_DEG +
                              (self.END_DEG - self.START_DEG) * (i + 1) / 48)
            p0 = (cx + self.RADIUS * math.cos(a0),
                  cy + self.RADIUS * math.sin(a0))
            p1 = (cx + self.RADIUS * math.cos(a1),
                  cy + self.RADIUS * math.sin(a1))
            dpg.draw_line(p0, p1, color=color, thickness=5,
                          parent=self._draw_tag)
        needle_angle = math.radians(
            self.START_DEG + (self.END_DEG - self.START_DEG) * frac)
        nx = cx + (self.RADIUS - 8) * math.cos(needle_angle)
        ny = cy + (self.RADIUS - 8) * math.sin(needle_angle)
        dpg.draw_line((cx, cy), (nx, ny), color=ACCENT_2, thickness=3,
                      parent=self._draw_tag)
        dpg.draw_circle((cx, cy), 4, color=ACCENT_2,
                        fill=ACCENT_2, parent=self._draw_tag)
        dpg.set_value(self._val_tag, f"{value:7.2f} {self.unit}")
