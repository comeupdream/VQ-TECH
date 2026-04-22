"""CSV datalogger — writes every snapshot in a background thread."""
import csv
import os
import threading
import time
from datetime import datetime
from typing import Callable, Dict, Iterable, Optional


class DataLogger:
    def __init__(self, columns: Iterable[str], log_dir: str = "logs"):
        self.columns = list(columns)
        self.log_dir = log_dir
        self._file = None
        self._writer: Optional[csv.DictWriter] = None
        self._path: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        os.makedirs(log_dir, exist_ok=True)

    @property
    def path(self) -> Optional[str]:
        return self._path

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, snapshot_fn: Callable[[], Dict[str, float]],
              interval: float = 0.1):
        if self.is_running:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = os.path.join(self.log_dir, f"vqtech_{ts}.csv")
        self._file = open(self._path, "w", newline="")
        self._writer = csv.DictWriter(
            self._file, fieldnames=["timestamp"] + self.columns)
        self._writer.writeheader()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, args=(snapshot_fn, interval), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None

    def _loop(self, snapshot_fn, interval):
        while not self._stop.is_set():
            row = {"timestamp": time.time()}
            snap = snapshot_fn()
            for col in self.columns:
                row[col] = snap.get(col, "")
            try:
                self._writer.writerow(row)
                self._file.flush()
            except ValueError:
                break
            time.sleep(interval)
