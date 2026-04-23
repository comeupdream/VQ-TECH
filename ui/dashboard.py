"""Dashboard layout — gauges grid, live graphs, datalog + tune-dump controls."""
from typing import List

import dearpygui.dearpygui as dpg

from config.pids import GAUGE_LAYOUT, STANDARD_PIDS, EXTENDED_PIDS
from config.theme import (ACCENT, ACCENT_2, DANGER, MUTED, TEXT, WARN,
                          apply_global_theme)
from core.datalogger import DataLogger
from core.obd_client import OBDClient
from core.tune_dumper import TuneDumper
from ui.gauges import Gauge
from ui.graphs import LiveGraph


GAUGE_COLS = 6
KMH_TO_MPH = 0.621371


class Dashboard:
    def __init__(self, client: OBDClient):
        self.client = client
        self.gauges: List[Gauge] = []
        self.graphs: List[LiveGraph] = []
        self.logger = DataLogger(
            list(STANDARD_PIDS.keys()) + list(EXTENDED_PIDS.keys()))
        self.dumper = TuneDumper()
        # Tag generation is deferred to build() because DPG 2.x requires
        # create_context() before generate_uuid() is legal.
        self._log_tag = 0
        self._status_tag = 0
        self._dump_log_tag = 0
        self._probe_table_tag = 0
        self._probe_status_tag = 0
        self._probe_row_tags: dict = {}
        self._last_version: int = -1
        self._hero_rpm_tag = 0
        self._hero_mph_tag = 0
        self._hero_coolant_tag = 0
        self._hero_intake_tag = 0
        self._hero_oil_tag = 0
        self._hero_batt_tag = 0

    def build(self):
        dpg.create_context()
        self._log_tag = dpg.generate_uuid()
        self._status_tag = dpg.generate_uuid()
        self._dump_log_tag = dpg.generate_uuid()
        self._probe_table_tag = dpg.generate_uuid()
        self._probe_status_tag = dpg.generate_uuid()
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
                with dpg.tab(label="PID Probe"):
                    self._build_probe()
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
            dpg.add_spacer(width=40)
            dpg.add_text("ECU: 7E0 / 7E8  |  ISO 15765-4 CAN 500k",
                         color=MUTED)
        dpg.add_separator()

    def _build_gauges(self):
        self._build_hero()
        dpg.add_separator()
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

    def _build_hero(self):
        """Oversized digital readouts that sit above the arc gauges."""
        with dpg.group(horizontal=True):
            # --- RPM (giant digital) ---
            with dpg.child_window(width=520, height=180, border=True,
                                  no_scrollbar=True):
                dpg.add_text("ENGINE RPM", color=MUTED)
                dl = dpg.generate_uuid()
                dpg.add_drawlist(width=500, height=140, tag=dl)
                self._hero_rpm_tag = dpg.generate_uuid()
                dpg.draw_text((30, 5), "----", color=ACCENT, size=120,
                              tag=self._hero_rpm_tag, parent=dl)

            # --- MPH (giant digital, converted from km/h) ---
            with dpg.child_window(width=360, height=180, border=True,
                                  no_scrollbar=True):
                dpg.add_text("SPEED  (MPH)", color=MUTED)
                dl = dpg.generate_uuid()
                dpg.add_drawlist(width=340, height=140, tag=dl)
                self._hero_mph_tag = dpg.generate_uuid()
                dpg.draw_text((80, 5), "--", color=ACCENT, size=120,
                              tag=self._hero_mph_tag, parent=dl)

            # --- Temps + battery (digital column) ---
            with dpg.child_window(width=300, height=180, border=True,
                                  no_scrollbar=True):
                dpg.add_text("TEMPS  /  BATT", color=MUTED)
                dpg.add_separator()
                self._hero_coolant_tag = dpg.generate_uuid()
                self._hero_intake_tag = dpg.generate_uuid()
                self._hero_oil_tag = dpg.generate_uuid()
                self._hero_batt_tag = dpg.generate_uuid()
                dpg.add_text("Coolant   --", tag=self._hero_coolant_tag,
                             color=TEXT)
                dpg.add_text("Intake    --", tag=self._hero_intake_tag,
                             color=TEXT)
                dpg.add_text("Oil       --", tag=self._hero_oil_tag,
                             color=TEXT)
                dpg.add_text("Battery   --", tag=self._hero_batt_tag,
                             color=TEXT)

    def _update_hero(self, snap):
        rpm = snap.get("RPM")
        speed = snap.get("SPEED")
        coolant = snap.get("COOLANT")
        intake = snap.get("INTAKE_TEMP")
        oil = snap.get("OIL_TEMP")
        batt = snap.get("BATT_V")

        dpg.configure_item(
            self._hero_rpm_tag,
            text="----" if rpm is None else f"{int(rpm):>4d}")
        dpg.configure_item(
            self._hero_mph_tag,
            text="--" if speed is None else f"{int(speed * KMH_TO_MPH):>3d}")

        if coolant is None:
            dpg.set_value(self._hero_coolant_tag, "Coolant   --")
        else:
            dpg.set_value(self._hero_coolant_tag,
                          f"Coolant  {coolant:5.1f} °C")
        if intake is None:
            dpg.set_value(self._hero_intake_tag, "Intake    --")
        else:
            dpg.set_value(self._hero_intake_tag,
                          f"Intake   {intake:5.1f} °C")
        if oil is None:
            dpg.set_value(self._hero_oil_tag, "Oil       --")
        else:
            dpg.set_value(self._hero_oil_tag, f"Oil      {oil:5.1f} °C")
        if batt is None:
            dpg.set_value(self._hero_batt_tag, "Battery   --")
        else:
            dpg.set_value(self._hero_batt_tag, f"Battery  {batt:5.2f} V")

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

    def _build_probe(self):
        dpg.add_text(
            "Query every PID once. OK = ECU responded, NO DATA = PID not "
            "supported by this ECU firmware. Unsupported PIDs are skipped "
            "in the main poll loop so the bus stays snappy.",
            color=MUTED, wrap=1400)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Probe PIDs", callback=self._run_probe,
                           tag="btn_probe", width=160)
            dpg.add_button(label="Re-enable All",
                           callback=self._reenable_all, width=160)
            dpg.add_text("", tag=self._probe_status_tag, color=MUTED)
        dpg.add_separator()
        all_keys = list(STANDARD_PIDS.keys()) + list(EXTENDED_PIDS.keys())
        with dpg.table(tag=self._probe_table_tag, header_row=True,
                       resizable=True, policy=dpg.mvTable_SizingStretchProp,
                       borders_innerH=True, borders_outerH=True,
                       borders_innerV=True, borders_outerV=True):
            dpg.add_table_column(label="PID")
            dpg.add_table_column(label="Mode")
            dpg.add_table_column(label="Status")
            dpg.add_table_column(label="Last Value")
            for key in all_keys:
                mode = "22 (Nissan)" if key in EXTENDED_PIDS else "01"
                with dpg.table_row():
                    dpg.add_text(key)
                    dpg.add_text(mode, color=MUTED)
                    status_tag = dpg.generate_uuid()
                    value_tag = dpg.generate_uuid()
                    dpg.add_text("—", tag=status_tag, color=MUTED)
                    dpg.add_text("—", tag=value_tag, color=MUTED)
                    self._probe_row_tags[key] = (status_tag, value_tag)

    def _run_probe(self):
        dpg.set_value(self._probe_status_tag, "Probing...")
        dpg.configure_item("btn_probe", enabled=False)
        import threading
        threading.Thread(target=self._probe_worker, daemon=True).start()

    def _probe_worker(self):
        results = self.client.probe()
        ok = sum(1 for v in results.values() if v.startswith(("OK", "DEMO")))
        total = len(results) or 1
        for key, status in results.items():
            if key not in self._probe_row_tags:
                continue
            status_tag, value_tag = self._probe_row_tags[key]
            if status.startswith("OK"):
                dpg.set_value(status_tag, "OK")
                dpg.configure_item(status_tag, color=ACCENT)
                dpg.set_value(value_tag, status[3:].strip())
                dpg.configure_item(value_tag, color=ACCENT)
            elif status.startswith("DEMO"):
                dpg.set_value(status_tag, "DEMO")
                dpg.configure_item(status_tag, color=WARN)
                dpg.set_value(value_tag, "simulated")
                dpg.configure_item(value_tag, color=MUTED)
            elif status == "NO DATA":
                dpg.set_value(status_tag, "NO DATA")
                dpg.configure_item(status_tag, color=DANGER)
                dpg.set_value(value_tag, "—")
                dpg.configure_item(value_tag, color=MUTED)
            else:
                dpg.set_value(status_tag, status)
                dpg.configure_item(status_tag, color=DANGER)
        dpg.set_value(self._probe_status_tag,
                      f"Done — {ok}/{total} PIDs responded.")
        dpg.configure_item("btn_probe", enabled=True)

    def _reenable_all(self):
        for k in self.client.supported:
            self.client.supported[k] = True
        dpg.set_value(self._probe_status_tag,
                      "All PIDs re-enabled in poll loop.")

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
        version = self.client.version()
        if version != self._last_version:
            self._last_version = version
            snap = self.client.snapshot()
            dpg.set_value(self._status_tag,
                          "DEMO" if self.client.demo else "CONNECTED")
            self._update_hero(snap)
            for g in self.gauges:
                g.update(snap.get(g.key))
            for lg in self.graphs:
                lg.push(snap)
        # Always render — needles animate smoothly toward the latest target.
        for g in self.gauges:
            g.render()

    def run(self):
        while dpg.is_dearpygui_running():
            self.tick()
            dpg.render_dearpygui_frame()
        self.logger.stop()
        self.client.stop()
        dpg.destroy_context()
