"""Dashboard layout — gauges grid, live graphs, datalog + tune-dump controls."""
from typing import List

import dearpygui.dearpygui as dpg

from config.pids import GAUGE_LAYOUT, STANDARD_PIDS, EXTENDED_PIDS
from config.theme import ACCENT, MUTED, apply_global_theme
from core.datalogger import DataLogger
from core.obd_client import OBDClient
from core.tune_dumper import TuneDumper
from ui.gauges import Gauge
from ui.graphs import LiveGraph


GAUGE_COLS = 4


class Dashboard:
    def __init__(self, client: OBDClient):
        self.client = client
        self.gauges: List[Gauge] = []
        self.graphs: List[LiveGraph] = []
        self.logger = DataLogger(
            list(STANDARD_PIDS.keys()) + list(EXTENDED_PIDS.keys()))
        self.dumper = TuneDumper()
        self._log_tag = dpg.generate_uuid()
        self._status_tag = dpg.generate_uuid()
        self._dump_log_tag = dpg.generate_uuid()

    def build(self):
        dpg.create_context()
        dpg.create_viewport(title="VQ-TECH — G37 VQ37VHR Dashboard",
                            width=1600, height=950)
        apply_global_theme()

        with dpg.window(tag="main", label="VQ-TECH",
                        no_title_bar=True, no_move=True, no_resize=True):
            self._build_header()
            with dpg.tab_bar():
                with dpg.tab(label="Gauges"):
                    self._build_gauges()
                with dpg.tab(label="Live Graphs"):
                    self._build_graphs()
                with dpg.tab(label="Datalog / Tune"):
                    self._build_controls()

        dpg.set_primary_window("main", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def _build_header(self):
        with dpg.group(horizontal=True):
            dpg.add_text("VQ-TECH", color=ACCENT)
            dpg.add_text("  |  Infiniti G37 Sport  |  VQ37VHR",
                         color=MUTED)
            dpg.add_spacer(width=40)
            dpg.add_text("STATUS:", color=MUTED)
            dpg.add_text("INITIALIZING", tag=self._status_tag, color=ACCENT)
        dpg.add_separator()

    def _build_gauges(self):
        row = []
        for entry in GAUGE_LAYOUT:
            key, label, vmin, vmax, danger, unit = entry
            g = Gauge(key, label, vmin, vmax, danger, unit)
            self.gauges.append(g)
            row.append(g)
            if len(row) == GAUGE_COLS:
                with dpg.group(horizontal=True):
                    for gg in row:
                        gg.build()
                row = []
        if row:
            with dpg.group(horizontal=True):
                for gg in row:
                    gg.build()

    def _build_graphs(self):
        groups = [
            (["RPM", "SPEED"], "Engine Speed / Vehicle Speed"),
            (["AFR_B1", "AFR_B2"], "Wideband Lambda (Bank 1 / Bank 2)"),
            (["TIMING_ADV", "KNOCK_CORR"], "Timing & Knock Correction"),
            (["VVEL_B1", "VVEL_B2", "CAM_ADV_B1", "CAM_ADV_B2"],
             "VVEL Lift + Cam Advance"),
            (["STFT_B1", "LTFT_B1", "STFT_B2", "LTFT_B2"], "Fuel Trims"),
            (["COOLANT", "OIL_TEMP", "INTAKE_TEMP"], "Temperatures"),
        ]
        for keys, title in groups:
            lg = LiveGraph(keys, title=title)
            self.graphs.append(lg)
            lg.build()

    def _build_controls(self):
        with dpg.group(horizontal=True):
            dpg.add_button(label="Start Datalog", callback=self._toggle_log,
                           tag="btn_log", width=160)
            dpg.add_text("", tag=self._log_tag, color=MUTED)
        dpg.add_separator()
        dpg.add_text("ROM Dump (nisprog + npkern via K+DCAN)",
                     color=ACCENT)
        with dpg.group(horizontal=True):
            dpg.add_input_text(label="Port", default_value="/dev/ttyUSB0",
                               tag="dump_port", width=200)
            dpg.add_input_int(label="ROM size (KB)", default_value=1024,
                              tag="dump_size", width=120)
            dpg.add_button(label="Dump Current Tune",
                           callback=self._dump_tune, width=200)
        with dpg.child_window(height=320, border=True):
            dpg.add_text("", tag=self._dump_log_tag, color=MUTED,
                         wrap=1400)

    def _toggle_log(self):
        if self.logger.is_running:
            self.logger.stop()
            dpg.set_item_label("btn_log", "Start Datalog")
            dpg.set_value(self._log_tag, f"Saved: {self.logger.path}")
        else:
            self.logger.start(self.client.snapshot, interval=0.1)
            dpg.set_item_label("btn_log", "Stop Datalog")
            dpg.set_value(self._log_tag, f"Logging to {self.logger.path}")

    def _dump_tune(self):
        self.dumper.port = dpg.get_value("dump_port")
        self.dumper.rom_size_kb = int(dpg.get_value("dump_size"))
        self._append_dump_log("Starting ROM dump...")
        self.dumper.dump(on_log=self._append_dump_log,
                         on_done=self._dump_done)

    def _append_dump_log(self, line: str):
        prev = dpg.get_value(self._dump_log_tag) or ""
        dpg.set_value(self._dump_log_tag, (prev + "\n" + line)[-8000:])

    def _dump_done(self, ok: bool, path: str):
        msg = f"Dump complete: {path}" if ok else "Dump FAILED."
        self._append_dump_log(msg)

    def tick(self):
        snap = self.client.snapshot()
        dpg.set_value(self._status_tag,
                      "DEMO" if self.client.demo else "CONNECTED")
        for g in self.gauges:
            g.update(snap.get(g.key))
        for lg in self.graphs:
            lg.push(snap)

    def run(self):
        while dpg.is_dearpygui_running():
            self.tick()
            dpg.render_dearpygui_frame()
        self.logger.stop()
        self.client.stop()
        dpg.destroy_context()
