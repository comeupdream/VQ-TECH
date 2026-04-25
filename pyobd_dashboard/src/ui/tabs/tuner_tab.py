import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import sys
import platform
import subprocess
from pathlib import Path

from ui.theme import ThemeManager

# Make project root importable so `core.tune_dumper` resolves
_src_dir = Path(__file__).parent.parent.parent
_project_root = _src_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class TunerTab:
    """ROM tune dumping with pre-flight test, progress, and hex viewer."""

    def __init__(self, parent_frame, app_instance):
        self.frame = parent_frame
        self.app = app_instance
        self.dumper = None
        self.last_dump_path = None

        self.frame.configure(fg_color=ThemeManager.get("BACKGROUND"))

        header = ctk.CTkLabel(
            self.frame,
            text="ECU Tune Dumping (nisprog)",
            font=("Arial", 18, "bold"),
            text_color=ThemeManager.get("ACCENT")
        )
        header.pack(pady=(15, 5))

        # ---- Configuration card ----
        config_frame = ctk.CTkFrame(self.frame, fg_color=ThemeManager.get("CARD_BG"))
        config_frame.pack(fill="x", padx=20, pady=10)

        # Row 1: Port + auto-detect
        row1 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(row1, text="Serial Port:", width=110, anchor="w",
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left")
        self.port_var = ctk.StringVar(value="COM3" if platform.system() == "Windows" else "/dev/ttyUSB0")
        self.port_combo = ctk.CTkComboBox(row1, variable=self.port_var, width=200,
                                          values=[self.port_var.get()],
                                          fg_color=ThemeManager.get("BACKGROUND"))
        self.port_combo.pack(side="left", padx=5)
        ctk.CTkButton(row1, text="Auto-Detect", width=110,
                      fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.auto_detect_port).pack(side="left", padx=5)

        # Row 2: Kernel
        row2 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row2, text="Kernel (.bin):", width=110, anchor="w",
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left")
        self.kernel_var = ctk.StringVar(value="")
        ctk.CTkEntry(row2, textvariable=self.kernel_var, width=320).pack(side="left", padx=5)
        ctk.CTkButton(row2, text="Browse", width=80,
                      fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.pick_kernel).pack(side="left", padx=5)

        # Row 3: ROM size + output dir
        row3 = ctk.CTkFrame(config_frame, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkLabel(row3, text="ROM Size (KB):", width=110, anchor="w",
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left")
        self.size_var = ctk.StringVar(value="1024")
        ctk.CTkEntry(row3, textvariable=self.size_var, width=80).pack(side="left", padx=5)
        ctk.CTkLabel(row3, text="Save To:", width=70, anchor="e",
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left", padx=(20, 5))
        self.out_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "tunes"))
        ctk.CTkEntry(row3, textvariable=self.out_var, width=200).pack(side="left", padx=5)
        ctk.CTkButton(row3, text="...", width=40,
                      fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.pick_output).pack(side="left", padx=5)

        # ---- Action buttons ----
        button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        button_frame.pack(pady=10)

        self.btn_ecuid = ctk.CTkButton(
            button_frame, text="READ ECU ID", width=140,
            fg_color=ThemeManager.get("ACCENT_DIM"),
            text_color=ThemeManager.get("TEXT_MAIN"),
            command=self.on_read_ecu_id)
        self.btn_ecuid.pack(side="left", padx=5)

        self.btn_test = ctk.CTkButton(
            button_frame, text="TEST CONNECTION", width=160,
            fg_color=ThemeManager.get("ACCENT_DIM"),
            text_color=ThemeManager.get("TEXT_MAIN"),
            command=self.on_test_click)
        self.btn_test.pack(side="left", padx=5)

        self.btn_dump = ctk.CTkButton(
            button_frame, text="START DUMP", width=160,
            fg_color=ThemeManager.get("ACCENT"),
            text_color=ThemeManager.get("BACKGROUND"),
            hover_color=ThemeManager.get("ACCENT_DIM"),
            command=self.on_dump_click)
        self.btn_dump.pack(side="left", padx=5)

        self.btn_hex = ctk.CTkButton(
            button_frame, text="HEX VIEWER", width=140,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_MAIN"),
            command=self.on_view_hex)
        self.btn_hex.pack(side="left", padx=5)

        self.btn_open_folder = ctk.CTkButton(
            button_frame, text="OPEN FOLDER", width=140,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_MAIN"),
            command=self.on_open_folder)
        self.btn_open_folder.pack(side="left", padx=5)

        # ---- Progress bar ----
        prog_frame = ctk.CTkFrame(self.frame, fg_color=ThemeManager.get("CARD_BG"))
        prog_frame.pack(fill="x", padx=20, pady=(5, 5))
        self.progress_label = ctk.CTkLabel(
            prog_frame, text="Idle",
            font=("Consolas", 11),
            text_color=ThemeManager.get("TEXT_DIM"))
        self.progress_label.pack(pady=(8, 2))
        self.progress_bar = ctk.CTkProgressBar(
            prog_frame, height=14,
            progress_color=ThemeManager.get("ACCENT"),
            fg_color=ThemeManager.get("BACKGROUND"))
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 10))
        self.progress_bar.set(0)

        # ---- Log textbox ----
        ctk.CTkLabel(
            self.frame, text="Operation Log:",
            font=("Arial", 12, "bold"),
            text_color=ThemeManager.get("TEXT_MAIN")
        ).pack(pady=(10, 4), padx=20, anchor="w")

        self.txt_log = ctk.CTkTextbox(
            self.frame, height=220,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_DIM"),
            font=("Consolas", 10))
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.txt_log.insert("1.0",
            "Ready.\n"
            "1. Plug K+DCAN into OBD port (K-Line switch position for nisprog)\n"
            "2. Ignition ON, engine OFF\n"
            "3. Click AUTO-DETECT to find serial port\n"
            "4. Pick kernel .bin matching your ECU\n"
            "5. Click TEST CONNECTION first to verify\n"
            "6. Click START DUMP for full ROM read\n\n"
            "nisprog must be on PATH (or set absolute path in config).\n"
        )

    # ------------------------------------------------------------------
    # Port detection
    # ------------------------------------------------------------------
    def auto_detect_port(self):
        """Enumerate serial ports and populate the combo box."""
        ports = []
        try:
            import serial.tools.list_ports
            for p in serial.tools.list_ports.comports():
                desc = f"{p.device}"
                if p.description and p.description != "n/a":
                    desc = f"{p.device}  ({p.description})"
                ports.append(desc)
        except ImportError:
            self.log("pyserial not installed; falling back to glob scan")
            if platform.system() == "Windows":
                ports = [f"COM{i}" for i in range(1, 17)]
            else:
                import glob
                ports = (glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*") +
                         glob.glob("/dev/tty.usbserial-*"))

        if not ports:
            self.log("No serial ports detected. Plug in your K+DCAN cable and try again.")
            return

        self.port_combo.configure(values=ports)
        # Pick the first FTDI/USB port if we can identify one
        ftdi = next((p for p in ports if "FTDI" in p.upper() or "USB" in p.upper()), ports[0])
        # Strip the description part for the actual port value
        self.port_var.set(ftdi.split("  ")[0])
        self.log(f"Found {len(ports)} port(s). Selected: {self.port_var.get()}")
        for p in ports:
            self.log(f"  - {p}")

    # ------------------------------------------------------------------
    # File pickers
    # ------------------------------------------------------------------
    def pick_kernel(self):
        path = filedialog.askopenfilename(
            title="Select npkern .bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
        if path:
            self.kernel_var.set(path)
            self.log(f"Kernel selected: {path}")

    def pick_output(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.out_var.set(path)

    # ------------------------------------------------------------------
    # nisprog actions
    # ------------------------------------------------------------------
    def _build_dumper(self):
        from core.tune_dumper import TuneDumper
        try:
            rom_size = int(self.size_var.get())
        except ValueError:
            self.log("ERROR: ROM size must be an integer (KB).")
            return None
        port = self.port_var.get().split("  ")[0].strip()
        return TuneDumper(
            nisprog_bin="nisprog",
            port=port,
            kernel_path=self.kernel_var.get().strip(),
            rom_size_kb=rom_size,
            out_dir=self.out_var.get().strip() or "tunes",
        )

    def on_read_ecu_id(self):
        self.dumper = self._build_dumper()
        if not self.dumper:
            return
        self.txt_log.delete("1.0", "end")
        self.btn_ecuid.configure(state="disabled", text="READING...")
        self.btn_test.configure(state="disabled")
        self.btn_dump.configure(state="disabled")
        self.set_progress(0, "Reading ECU identifier (no kernel needed)...")
        self.dumper.read_ecu_id(
            on_log=self._safe_log,
            on_done=self._on_ecu_id_done)

    def _on_ecu_id_done(self, ok: bool, output: str):
        self.frame.after(0, lambda: self.btn_ecuid.configure(state="normal", text="READ ECU ID"))
        self.frame.after(0, lambda: self.btn_test.configure(state="normal"))
        self.frame.after(0, lambda: self.btn_dump.configure(state="normal"))

        ids = self._parse_ecu_identifiers(output)

        if ok and ids:
            self.frame.after(0, lambda: self.set_progress(0, "✓ ECU identified"))
            self._safe_log("\n" + "=" * 50)
            self._safe_log("DETECTED ECU IDENTIFIERS:")
            for label, value in ids.items():
                self._safe_log(f"  {label:14s} {value}")
            self._safe_log("=" * 50)
            self._safe_log("\nNext step: search for an npkern .bin matching this ECU.")
            self._safe_log("VQ37 G37 ECUs typically use SH7058 - look for 'npk_sh7058.bin'.")
            self._safe_log("Communities to search: NICOclub, RomRaider, GitHub.")
        elif ok:
            self.frame.after(0, lambda: self.set_progress(0, "Reply received - check log"))
            self._safe_log("\nNo recognized ECU ID pattern in output. Inspect raw response above.")
        else:
            self.frame.after(0, lambda: self.set_progress(0, "✗ ECU did not respond"))
            self._safe_log("\n✗ Failed. Check cable, K-Line switch position, ignition ON.")

    def _parse_ecu_identifiers(self, text: str) -> dict:
        """Extract ECU ID, part number, and Cal ID from nisprog output."""
        import re
        found = {}

        # Nissan part number pattern: 23710-XXXXX
        m = re.search(r"\b(237\d{2}[\s\-][A-Z0-9]{4,5})\b", text)
        if m:
            found["Part Number:"] = m.group(1).replace(" ", "-")

        # nisprog often prints "ECU ID: <hex>"
        m = re.search(r"ECU\s*ID[:\s]+([0-9A-Fa-f\s]{4,})", text)
        if m:
            found["ECU ID (hex):"] = m.group(1).strip()

        # Cal ID: ASCII string after "CAL" or "Cal ID"
        m = re.search(r"[Cc]al(?:ibration)?\s*[Ii][Dd][:\s]+([A-Za-z0-9\-_]{3,16})", text)
        if m:
            found["Cal ID:"] = m.group(1)

        # ECU type / hardware string
        m = re.search(r"(SH70[0-9]{2})", text)
        if m:
            found["Chip Family:"] = m.group(1)

        return found

    def on_test_click(self):
        self.dumper = self._build_dumper()
        if not self.dumper:
            return
        self.txt_log.delete("1.0", "end")
        self.btn_test.configure(state="disabled", text="TESTING...")
        self.btn_dump.configure(state="disabled")
        self.btn_ecuid.configure(state="disabled")
        self.set_progress(0, "Pre-flight test...")
        self.dumper.test_connection(
            on_log=self._safe_log,
            on_done=self._on_test_done)

    def _on_test_done(self, ok: bool, output: str):
        self.frame.after(0, lambda: self.btn_test.configure(state="normal", text="TEST CONNECTION"))
        self.frame.after(0, lambda: self.btn_dump.configure(state="normal"))
        self.frame.after(0, lambda: self.btn_ecuid.configure(state="normal"))
        if ok:
            self.frame.after(0, lambda: self.set_progress(0, "✓ ECU responded - ready to dump"))
            self._safe_log("\n✓ Pre-flight OK. Safe to attempt full dump.")
        else:
            self.frame.after(0, lambda: self.set_progress(0, "✗ ECU did not respond"))
            self._safe_log("\n✗ Pre-flight FAILED. Check:")
            self._safe_log("  - K+DCAN switch position (K-Line for nisprog)")
            self._safe_log("  - Ignition is ON")
            self._safe_log("  - Correct serial port selected")
            self._safe_log("  - Kernel .bin matches your ECU")

    def on_dump_click(self):
        self.dumper = self._build_dumper()
        if not self.dumper:
            return
        self.txt_log.delete("1.0", "end")
        self.btn_dump.configure(state="disabled", text="DUMPING...")
        self.btn_test.configure(state="disabled")
        self.btn_ecuid.configure(state="disabled")
        self.set_progress(0, "Starting dump...")
        self.dumper.dump(
            on_log=self._safe_log,
            on_progress=self._on_progress,
            on_done=self._on_dump_done)

    def _on_progress(self, pct: float, current: int, total: int):
        kb_now = current / 1024.0
        kb_total = total / 1024.0
        msg = f"{pct:5.1f}%  {kb_now:.1f} / {kb_total:.0f} KB"
        self.frame.after(0, lambda: self.set_progress(pct / 100.0, msg))

    def _on_dump_done(self, ok: bool, filepath: str):
        self.frame.after(0, lambda: self.btn_dump.configure(state="normal", text="START DUMP"))
        self.frame.after(0, lambda: self.btn_test.configure(state="normal"))
        self.frame.after(0, lambda: self.btn_ecuid.configure(state="normal"))
        if ok:
            self.last_dump_path = filepath
            size_kb = os.path.getsize(filepath) / 1024.0
            self.frame.after(0, lambda: self.set_progress(1.0, f"✓ Dumped {size_kb:.1f} KB"))
            self._safe_log(f"\n✓ SUCCESS: {filepath} ({size_kb:.1f} KB)")
            self._safe_log("Click HEX VIEWER to inspect the dump.")
        else:
            self.frame.after(0, lambda: self.set_progress(0, "✗ Dump failed"))
            self._safe_log("\n✗ Dump did not complete.")

    # ------------------------------------------------------------------
    # Hex viewer
    # ------------------------------------------------------------------
    def on_view_hex(self):
        path = self.last_dump_path
        if not path or not os.path.exists(path):
            path = filedialog.askopenfilename(
                title="Open ROM .bin",
                initialdir=self.out_var.get().strip() or os.path.expanduser("~"),
                filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
            if not path:
                return
        HexViewer(self.frame, path)

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------
    def on_open_folder(self):
        out = self.out_var.get().strip() or "tunes"
        try:
            os.makedirs(out, exist_ok=True)
            if platform.system() == "Darwin":
                subprocess.Popen(["open", out])
            elif platform.system() == "Windows":
                os.startfile(out)
            else:
                subprocess.Popen(["xdg-open", out])
            self.log(f"Opened: {os.path.abspath(out)}")
        except Exception as e:
            self.log(f"Error opening folder: {e}")

    def set_progress(self, fraction: float, text: str):
        try:
            self.progress_bar.set(max(0.0, min(1.0, fraction)))
            self.progress_label.configure(text=text)
        except Exception:
            pass

    def log(self, message: str):
        try:
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")
        except Exception:
            pass

    def _safe_log(self, message: str):
        """Thread-safe log that marshals onto the Tk main thread."""
        self.frame.after(0, lambda: self.log(message))


# ----------------------------------------------------------------------
# Hex viewer modal
# ----------------------------------------------------------------------
class HexViewer(ctk.CTkToplevel):
    """Read-only hex+ASCII viewer with offset jump and pagination."""

    PAGE_SIZE = 4096  # bytes per page
    BYTES_PER_LINE = 16

    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.title(f"Hex Viewer — {os.path.basename(file_path)}")
        self.geometry("960x600")
        self.configure(fg_color=ThemeManager.get("BACKGROUND"))
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.offset = 0

        # ---- Toolbar ----
        toolbar = ctk.CTkFrame(self, fg_color=ThemeManager.get("CARD_BG"))
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(toolbar, text=f"File: {file_path}",
                     text_color=ThemeManager.get("TEXT_DIM"),
                     font=("Consolas", 10)).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(toolbar, text=f"  {self.file_size:,} bytes",
                     text_color=ThemeManager.get("ACCENT"),
                     font=("Consolas", 10, "bold")).pack(side="left", pady=8)

        ctk.CTkButton(toolbar, text="◀ Prev", width=70,
                      fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.prev_page).pack(side="right", padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Next ▶", width=70,
                      fg_color=ThemeManager.get("ACCENT_DIM"),
                      command=self.next_page).pack(side="right", padx=5, pady=5)

        # Jump-to-offset
        ctk.CTkLabel(toolbar, text="Goto 0x",
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="right", padx=(15, 0))
        self.goto_var = ctk.StringVar(value="0")
        goto_entry = ctk.CTkEntry(toolbar, textvariable=self.goto_var, width=100)
        goto_entry.pack(side="right", padx=5)
        goto_entry.bind("<Return>", lambda e: self.goto_offset())
        ctk.CTkButton(toolbar, text="Go", width=50,
                      fg_color=ThemeManager.get("ACCENT"),
                      text_color=ThemeManager.get("BACKGROUND"),
                      command=self.goto_offset).pack(side="right", padx=5)

        # ---- Hex display ----
        self.txt = ctk.CTkTextbox(
            self,
            font=("Consolas", 11),
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_MAIN"))
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Status bar
        self.status_var = tk.StringVar()
        ctk.CTkLabel(self, textvariable=self.status_var,
                     text_color=ThemeManager.get("TEXT_DIM"),
                     font=("Consolas", 10)).pack(pady=(0, 8))

        self.render_page()
        self.lift()
        self.focus_force()

    def render_page(self):
        try:
            with open(self.file_path, "rb") as f:
                f.seek(self.offset)
                data = f.read(self.PAGE_SIZE)
        except Exception as e:
            self.txt.delete("1.0", "end")
            self.txt.insert("1.0", f"Error reading file: {e}")
            return

        lines = []
        # Header
        hex_cols = " ".join(f"{i:02X}" for i in range(self.BYTES_PER_LINE))
        lines.append(f"OFFSET    {hex_cols}  ASCII")
        lines.append("-" * (10 + 3 * self.BYTES_PER_LINE + 2 + self.BYTES_PER_LINE))

        for i in range(0, len(data), self.BYTES_PER_LINE):
            chunk = data[i:i + self.BYTES_PER_LINE]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            hex_str = hex_str.ljust(self.BYTES_PER_LINE * 3 - 1)
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{self.offset + i:08X}  {hex_str}  {ascii_str}")

        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(lines))

        page_num = (self.offset // self.PAGE_SIZE) + 1
        total_pages = max(1, (self.file_size + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.status_var.set(
            f"Page {page_num}/{total_pages}  |  Offset 0x{self.offset:08X}  |  "
            f"Showing {len(data)} bytes")

    def next_page(self):
        if self.offset + self.PAGE_SIZE < self.file_size:
            self.offset += self.PAGE_SIZE
            self.render_page()

    def prev_page(self):
        if self.offset >= self.PAGE_SIZE:
            self.offset -= self.PAGE_SIZE
            self.render_page()
        else:
            self.offset = 0
            self.render_page()

    def goto_offset(self):
        raw = self.goto_var.get().strip().lower().lstrip("0x")
        try:
            target = int(raw, 16) if raw else 0
        except ValueError:
            self.status_var.set("Invalid hex offset")
            return
        target = max(0, min(target, max(0, self.file_size - 1)))
        # Snap to page boundary
        self.offset = (target // self.PAGE_SIZE) * self.PAGE_SIZE
        self.render_page()
