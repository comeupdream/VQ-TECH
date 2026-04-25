"""
ROM dump via nisprog over K+DCAN, using nisprog's interactive command-script mode (-f flag).

nisprog is an interactive shell, so we generate a temporary script with
setdev/npconn/dumpmem/quit and feed it to nisprog -f <script>.

All operations run on background threads so the UI stays responsive.
"""
import os
import shlex
import subprocess
import threading
import tempfile
import time
from datetime import datetime
from typing import Callable, Optional


class TuneDumper:
    """Drives nisprog to read ECU ROM via K+DCAN/K-Line."""

    def __init__(self, nisprog_bin: str = "nisprog",
                 port: str = "COM3",
                 kernel_path: str = "",
                 rom_size_kb: int = 1024,
                 out_dir: str = "tunes"):
        self.nisprog_bin = nisprog_bin
        self.port = port
        self.kernel_path = kernel_path
        self.rom_size_kb = rom_size_kb
        self.rom_size_bytes = rom_size_kb * 1024
        self.out_dir = out_dir
        self._thread: Optional[threading.Thread] = None
        self._proc: Optional[subprocess.Popen] = None
        self._stop_progress = False
        os.makedirs(out_dir, exist_ok=True)

    def _write_script(self, lines):
        """Write a temp command script for nisprog -f and return its path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".np", delete=False)
        f.write("\n".join(lines) + "\n")
        f.close()
        return f.name

    def read_ecu_id(self, on_log: Callable[[str], None],
                    on_done: Callable[[bool, str], None]):
        """Read ECU ID via standard diagnostic protocol. No kernel upload required.

        Useful for identifying the ECU hardware before sourcing a matching kernel.
        """
        if self._thread and self._thread.is_alive():
            on_log("Operation already in progress.")
            return
        self._thread = threading.Thread(
            target=self._run_ecu_id, args=(on_log, on_done), daemon=True)
        self._thread.start()

    def _run_ecu_id(self, on_log, on_done):
        # No kernel, no npconn - just initialize and read identifier
        cmds = [
            f"setdev 0 {self.port}",
            "ecuid",
            "quit",
        ]
        script_path = self._write_script(cmds)
        on_log("--- ECU ID read script ---")
        for ln in cmds:
            on_log(f"  {ln}")
        try:
            cmd = [self.nisprog_bin, "-f", script_path]
            on_log(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            output_lines = []
            for line in proc.stdout:
                line = line.rstrip()
                output_lines.append(line)
                on_log(line)
            proc.wait()
            full = "\n".join(output_lines)
            ok = proc.returncode == 0 and "error" not in full.lower()
            on_done(ok, full)
        except FileNotFoundError:
            on_log(f"nisprog binary not found at '{self.nisprog_bin}'. Add it to PATH.")
            on_done(False, "")
        except Exception as e:
            on_log(f"Error: {e}")
            on_done(False, "")
        finally:
            try: os.unlink(script_path)
            except Exception: pass

    def test_connection(self, on_log: Callable[[str], None],
                        on_done: Callable[[bool, str], None]):
        """Quick handshake: setdev -> npconn -> ecuid -> quit. No ROM read."""
        if self._thread and self._thread.is_alive():
            on_log("Operation already in progress.")
            return
        self._thread = threading.Thread(
            target=self._run_test, args=(on_log, on_done), daemon=True)
        self._thread.start()

    def _run_test(self, on_log, on_done):
        cmds = [f"setdev 0 {self.port}"]
        if self.kernel_path:
            cmds.append(f'set kernel "{self.kernel_path}"')
        cmds += ["npconn", "ecuid", "quit"]

        script_path = self._write_script(cmds)
        on_log("--- Pre-flight test script ---")
        for ln in cmds:
            on_log(f"  {ln}")
        try:
            cmd = [self.nisprog_bin, "-f", script_path]
            on_log(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            output_lines = []
            for line in proc.stdout:
                line = line.rstrip()
                output_lines.append(line)
                on_log(line)
            proc.wait()

            full = "\n".join(output_lines).lower()
            ok = (proc.returncode == 0 and
                  ("ecuid" in full or "ecu id" in full or "connected" in full)
                  and "error" not in full and "fail" not in full)
            on_done(ok, "\n".join(output_lines))
        except FileNotFoundError:
            on_log(f"nisprog binary not found at '{self.nisprog_bin}'. Add it to PATH.")
            on_done(False, "")
        except Exception as e:
            on_log(f"Error: {e}")
            on_done(False, "")
        finally:
            try: os.unlink(script_path)
            except Exception: pass

    def dump(self, on_log: Callable[[str], None],
             on_progress: Callable[[float, int, int], None],
             on_done: Callable[[bool, str], None]):
        """Full ROM dump. on_progress receives (pct, current_bytes, total_bytes)."""
        if self._thread and self._thread.is_alive():
            on_log("Dump already in progress.")
            return
        self._thread = threading.Thread(
            target=self._run_dump, args=(on_log, on_progress, on_done), daemon=True)
        self._thread.start()

    def _run_dump(self, on_log, on_progress, on_done):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(self.out_dir, f"rom_{ts}.bin")

        cmds = [f"setdev 0 {self.port}"]
        if self.kernel_path:
            cmds.append(f'set kernel "{self.kernel_path}"')
        cmds += [
            "npconn",
            f'dumpmem 0 0x{self.rom_size_bytes:X} "{out_path}"',
            "quit",
        ]

        script_path = self._write_script(cmds)
        on_log("--- Dump script ---")
        for ln in cmds:
            on_log(f"  {ln}")

        self._stop_progress = False
        progress_thread = threading.Thread(
            target=self._monitor_progress,
            args=(out_path, on_progress),
            daemon=True)
        progress_thread.start()

        try:
            cmd = [self.nisprog_bin, "-f", script_path]
            on_log(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT, text=True)
            for line in self._proc.stdout:
                on_log(line.rstrip())
            self._proc.wait()
            self._stop_progress = True
            progress_thread.join(timeout=1.0)

            file_ok = os.path.exists(out_path) and \
                      os.path.getsize(out_path) >= int(self.rom_size_bytes * 0.95)
            ok = self._proc.returncode == 0 and file_ok
            on_done(ok, out_path if ok else "")
        except FileNotFoundError:
            self._stop_progress = True
            on_log(f"nisprog binary not found at '{self.nisprog_bin}'. Add it to PATH.")
            on_done(False, "")
        except Exception as e:
            self._stop_progress = True
            on_log(f"Error: {e}")
            on_done(False, "")
        finally:
            try: os.unlink(script_path)
            except Exception: pass
            self._proc = None

    def _monitor_progress(self, out_path, on_progress):
        last_size = -1
        while not self._stop_progress:
            try:
                if os.path.exists(out_path):
                    size = os.path.getsize(out_path)
                    if size != last_size:
                        pct = min(100.0, (size / self.rom_size_bytes) * 100.0)
                        on_progress(pct, size, self.rom_size_bytes)
                        last_size = size
            except Exception:
                pass
            time.sleep(0.25)
        try:
            if os.path.exists(out_path):
                size = os.path.getsize(out_path)
                pct = min(100.0, (size / self.rom_size_bytes) * 100.0)
                on_progress(pct, size, self.rom_size_bytes)
        except Exception:
            pass

    def cancel(self):
        if self._proc:
            try: self._proc.terminate()
            except Exception: pass
        self._stop_progress = True
