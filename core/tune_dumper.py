"""
Stub for ROM dump via nisprog + npkern over K+DCAN (future integration).

Wire this to a button later. Everything runs off the main thread via
threading so the UI stays responsive.
"""
import os
import shlex
import subprocess
import threading
from datetime import datetime
from typing import Callable, Optional


class TuneDumper:
    """Wraps nisprog/npkern for ROM reads.

    Typical flow (FTDI K+DCAN cable at 10416 bps for Nissan SSM/Kline,
    adjust for your ECU):
        1. npkern kernel upload (one-time per session).
        2. nisprog 'readrom' with the proper ROM size (usually 1 MB for VQ37).
    """

    def __init__(self, nisprog_bin: str = "nisprog",
                 port: str = "/dev/ttyUSB0",
                 rom_size_kb: int = 1024,
                 out_dir: str = "tunes"):
        self.nisprog_bin = nisprog_bin
        self.port = port
        self.rom_size_kb = rom_size_kb
        self.out_dir = out_dir
        self._thread: Optional[threading.Thread] = None
        os.makedirs(out_dir, exist_ok=True)

    def dump(self, on_log: Callable[[str], None],
             on_done: Callable[[bool, str], None]):
        if self._thread and self._thread.is_alive():
            on_log("Dump already in progress.")
            return
        self._thread = threading.Thread(
            target=self._run, args=(on_log, on_done), daemon=True)
        self._thread.start()

    def _run(self, on_log, on_done):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(self.out_dir, f"rom_{ts}.bin")
        cmd = [
            self.nisprog_bin,
            "-p", self.port,
            "-r", f"0:{self.rom_size_kb * 1024}",
            "-o", out_path,
        ]
        on_log(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                on_log(line.rstrip())
            proc.wait()
            ok = proc.returncode == 0 and os.path.exists(out_path)
            on_done(ok, out_path if ok else "")
        except FileNotFoundError:
            on_log(f"nisprog binary not found at '{self.nisprog_bin}'.")
            on_done(False, "")
        except Exception as e:
            on_log(f"Error: {e}")
            on_done(False, "")
