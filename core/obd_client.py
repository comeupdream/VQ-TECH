"""Thin python-obd wrapper with async polling + demo mode."""
import math
import random
import threading
import time
from typing import Dict, Optional

import obd

from config.pids import STANDARD_PIDS, EXTENDED_PIDS


class OBDClient:
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400,
                 demo: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.demo = demo
        self._conn: Optional[obd.OBD] = None
        self._values: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._commands = {**STANDARD_PIDS, **EXTENDED_PIDS}

    def connect(self) -> bool:
        if self.demo:
            return True
        obd.logger.setLevel(obd.logging.WARNING)
        self._conn = obd.OBD(portstr=self.port, baudrate=self.baudrate,
                             fast=False, timeout=1.0)
        if self._conn.is_connected():
            for cmd in EXTENDED_PIDS.values():
                self._conn.supported_commands.add(cmd)
            return True
        return False

    def start(self, interval: float = 0.1):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, args=(interval,),
                                        daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._conn:
            self._conn.close()

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._values)

    def _loop(self, interval: float):
        while not self._stop.is_set():
            t0 = time.time()
            new = self._poll_demo() if self.demo else self._poll_real()
            with self._lock:
                self._values.update(new)
            elapsed = time.time() - t0
            time.sleep(max(0.0, interval - elapsed))

    def _poll_real(self) -> Dict[str, float]:
        out = {}
        for key, cmd in self._commands.items():
            try:
                r = self._conn.query(cmd, force=True)
                if r and not r.is_null() and r.value is not None:
                    out[key] = float(getattr(r.value, "magnitude", r.value))
            except Exception:
                continue
        return out

    def _poll_demo(self) -> Dict[str, float]:
        t = time.time()
        rpm = 2500 + 2500 * (0.5 + 0.5 * math.sin(t * 0.7))
        thr = max(0, 50 + 50 * math.sin(t * 0.9))
        load = thr * 0.9
        return {
            "RPM": rpm,
            "SPEED": 60 + 40 * math.sin(t * 0.3),
            "THROTTLE": thr,
            "COOLANT": 88 + random.uniform(-1, 2),
            "INTAKE_TEMP": 35 + random.uniform(-2, 2),
            "MAF": 5 + load * 0.4,
            "TIMING_ADV": 18 + 10 * math.sin(t * 1.2),
            "STFT_B1": random.uniform(-4, 4),
            "STFT_B2": random.uniform(-4, 4),
            "LTFT_B1": random.uniform(-6, 6),
            "LTFT_B2": random.uniform(-6, 6),
            "LOAD": load,
            "AFR_B1": 0.98 + 0.05 * math.sin(t * 1.5),
            "AFR_B2": 0.98 + 0.05 * math.cos(t * 1.4),
            "KNOCK_CORR": min(0, -abs(random.gauss(0, 1.2))),
            "VVEL_B1": 20 + 25 * (thr / 100),
            "VVEL_B2": 20 + 25 * (thr / 100),
            "CAM_ADV_B1": 15 * math.sin(t * 0.8),
            "CAM_ADV_B2": 15 * math.sin(t * 0.8 + 0.2),
            "INJ_PW_B1": 2 + load * 0.08,
            "INJ_PW_B2": 2 + load * 0.08,
            "OIL_TEMP": 95 + random.uniform(-1, 3),
            "BATT_V": 14.1 + random.uniform(-0.15, 0.15),
            "MAF_V": 1.0 + load * 0.03,
        }
