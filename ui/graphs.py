"""Live multi-graph rolling-buffer plot."""
import time
from collections import deque
from typing import Dict, Iterable

import dearpygui.dearpygui as dpg

from config.theme import ACCENT, ACCENT_2, WARN, DANGER, plot_theme

SERIES_COLORS = [ACCENT, ACCENT_2, WARN, DANGER,
                 (120, 200, 255), (255, 120, 255)]


class LiveGraph:
    def __init__(self, keys: Iterable[str], window_seconds: float = 30.0,
                 sample_rate_hz: float = 10.0, title: str = "Live Data"):
        self.keys = list(keys)
        self.window = window_seconds
        self.maxlen = int(window_seconds * sample_rate_hz)
        self.title = title
        self._t: deque = deque(maxlen=self.maxlen)
        self._series: Dict[str, deque] = {
            k: deque(maxlen=self.maxlen) for k in self.keys
        }
        self._series_tags: Dict[str, int] = {}
        self._x_axis = dpg.generate_uuid()
        self._y_axis = dpg.generate_uuid()
        self._t0 = time.time()

    def build(self, width: int = -1, height: int = 280):
        with dpg.plot(label=self.title, width=width, height=height,
                      anti_aliased=True):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="time (s)", tag=self._x_axis)
            dpg.add_plot_axis(dpg.mvYAxis, label="value", tag=self._y_axis)
            for i, k in enumerate(self.keys):
                tag = dpg.generate_uuid()
                dpg.add_line_series([], [], label=k, parent=self._y_axis,
                                    tag=tag)
                self._series_tags[k] = tag
                with dpg.theme() as th:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(
                            dpg.mvPlotCol_Line,
                            SERIES_COLORS[i % len(SERIES_COLORS)],
                            category=dpg.mvThemeCat_Plots)
                        dpg.add_theme_style(
                            dpg.mvPlotStyleVar_LineWeight, 2,
                            category=dpg.mvThemeCat_Plots)
                dpg.bind_item_theme(tag, th)

    def push(self, snapshot: Dict[str, float]):
        t = time.time() - self._t0
        self._t.append(t)
        for k in self.keys:
            self._series[k].append(snapshot.get(k, float("nan")))
        xs = list(self._t)
        for k in self.keys:
            dpg.set_value(self._series_tags[k], [xs, list(self._series[k])])
        if xs:
            dpg.set_axis_limits(self._x_axis, max(0, xs[-1] - self.window),
                                xs[-1] + 0.1)
            dpg.set_axis_limits_auto(self._y_axis)
