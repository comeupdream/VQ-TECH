"""Circular-arc gauge widget (DPG 2.x safe, high-performance).

Drawing is done ONCE in build(); update() only re-colors the tagged
segments and rotates the needle via configure_item — no delete/redraw.
"""
import math
from typing import List, Optional

import dearpygui.dearpygui as dpg

from config.theme import ACCENT, ACCENT_2, DANGER, MUTED, TEXT, WARN


class Gauge:
    SIZE = 220
    CENTER = 110
    RADIUS = 78
    NUM_SEGMENTS = 40
    NUM_TICKS = 6
    START_DEG = -225   # bottom-left, sweep clockwise 270° to bottom-right
    END_DEG = 45

    def __init__(self, key: str, label: str,
                 vmin: float, vmax: float, danger_above: float, unit: str):
        self.key = key
        self.label = label
        self.vmin = vmin
        self.vmax = vmax
        self.danger_above = danger_above
        self.unit = unit
        self._draw_tag = 0
        self._val_tag = 0
        self._needle_tag = 0
        self._segment_tags: List[int] = []
        self._target_frac: float = 0.0
        self._display_frac: float = 0.0
        self._target_value: Optional[float] = None

    def _angle(self, frac: float) -> float:
        return math.radians(self.START_DEG +
                            (self.END_DEG - self.START_DEG) * frac)

    def _pt(self, frac: float, r: float):
        a = self._angle(frac)
        return (self.CENTER + r * math.cos(a),
                self.CENTER + r * math.sin(a))

    def _fmt_tick(self, v: float) -> str:
        if self.vmax >= 1000:
            return f"{v/1000:.1f}k" if abs(v) >= 1000 else f"{int(v)}"
        span = self.vmax - self.vmin
        if span < 10:
            return f"{v:.1f}"
        return f"{int(v)}"

    def _fmt_value(self, v: float) -> str:
        if self.unit in ("rpm", "km/h", "mph"):
            return f"{v:6.0f} {self.unit}"
        if self.unit in ("°C", "°F", "%"):
            return f"{v:6.1f} {self.unit}"
        return f"{v:6.2f} {self.unit}"

    def build(self):
        with dpg.child_window(width=self.SIZE + 10,
                              height=self.SIZE + 50, border=True,
                              no_scrollbar=True):
            dpg.add_text(self.label, color=MUTED)
            self._draw_tag = dpg.generate_uuid()
            self._val_tag = dpg.generate_uuid()
            dpg.add_drawlist(width=self.SIZE, height=self.SIZE,
                             tag=self._draw_tag)
            dpg.add_text("--", tag=self._val_tag, color=TEXT)

        # --- background arc (pre-created segments, we'll re-color these) ---
        self._segment_tags = []
        for i in range(self.NUM_SEGMENTS):
            p0 = self._pt(i / self.NUM_SEGMENTS, self.RADIUS)
            p1 = self._pt((i + 1) / self.NUM_SEGMENTS, self.RADIUS)
            tag = dpg.generate_uuid()
            dpg.draw_line(p0, p1, color=(60, 70, 80, 255), thickness=3,
                          parent=self._draw_tag, tag=tag)
            self._segment_tags.append(tag)

        # --- major tick marks + numeric labels ---
        for i in range(self.NUM_TICKS + 1):
            frac = i / self.NUM_TICKS
            p_out = self._pt(frac, self.RADIUS + 7)
            p_in = self._pt(frac, self.RADIUS - 5)
            dpg.draw_line(p_in, p_out, color=TEXT, thickness=2,
                          parent=self._draw_tag)
            tick_val = self.vmin + (self.vmax - self.vmin) * frac
            p_lbl = self._pt(frac, self.RADIUS + 16)
            dpg.draw_text((p_lbl[0] - 10, p_lbl[1] - 7),
                          self._fmt_tick(tick_val),
                          color=MUTED, size=12, parent=self._draw_tag)

        # --- needle + pivot (dynamic, updated per frame via configure_item) ---
        p_cen = (self.CENTER, self.CENTER)
        p_tip = self._pt(0.0, self.RADIUS - 10)
        self._needle_tag = dpg.generate_uuid()
        dpg.draw_line(p_cen, p_tip, color=ACCENT_2, thickness=3,
                      parent=self._draw_tag, tag=self._needle_tag)
        dpg.draw_circle(p_cen, 5, color=ACCENT_2, fill=ACCENT_2,
                        parent=self._draw_tag)

    def update(self, value: Optional[float]):
        """Called when new polled data arrives — sets the target only."""
        self._target_value = value
        if value is None:
            self._target_frac = 0.0
        else:
            span = self.vmax - self.vmin or 1.0
            clamped = max(self.vmin, min(self.vmax, value))
            self._target_frac = (clamped - self.vmin) / span

    def render(self, lerp: float = 0.18):
        """Called every UI frame — animates needle smoothly toward target.

        lerp in (0,1]: higher = snappier. 0.18 at 60 FPS settles in ~15
        frames (~250 ms) which feels alive without jitter.
        """
        delta = self._target_frac - self._display_frac
        if abs(delta) < 0.001:
            self._display_frac = self._target_frac
        else:
            self._display_frac += delta * lerp

        frac = self._display_frac
        span = self.vmax - self.vmin or 1.0
        danger_frac = max(0.0, min(1.0, (self.danger_above - self.vmin) / span))
        warn_frac = max(0.0, danger_frac - 0.15)

        for i, tag in enumerate(self._segment_tags):
            seg_end = (i + 1) / self.NUM_SEGMENTS
            if seg_end > frac:
                dpg.configure_item(tag, color=(60, 70, 80, 255), thickness=3)
            else:
                if seg_end >= danger_frac:
                    color = DANGER
                elif seg_end >= warn_frac:
                    color = WARN
                else:
                    color = ACCENT
                dpg.configure_item(tag, color=color, thickness=6)

        p_tip = self._pt(frac, self.RADIUS - 10)
        dpg.configure_item(self._needle_tag,
                           p1=(self.CENTER, self.CENTER), p2=p_tip)

        if self._target_value is None:
            dpg.set_value(self._val_tag, "--")
        else:
            dpg.set_value(self._val_tag, self._fmt_value(self._target_value))
