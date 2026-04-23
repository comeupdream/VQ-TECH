import customtkinter as ctk
import threading
import os
import sys
from pathlib import Path

from ui.theme import ThemeManager

# Add parent directories to path for core imports
_src_dir = Path(__file__).parent.parent.parent
_project_root = _src_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class TunerTab:
    """ROM tune dumping and tuning interface."""

    def __init__(self, parent_frame, app_instance):
        self.frame = parent_frame
        self.app = app_instance
        self.dumper = None

        self.frame.configure(fg_color=ThemeManager.get("BACKGROUND"))

        # Header
        header = ctk.CTkLabel(
            self.frame,
            text="ECU Tune Dumping & Tuning",
            font=("Arial", 18, "bold"),
            text_color=ThemeManager.get("ACCENT")
        )
        header.pack(pady=15)

        # Configuration Frame
        config_frame = ctk.CTkFrame(self.frame, fg_color=ThemeManager.get("CARD_BG"))
        config_frame.pack(fill="x", padx=20, pady=10)

        # Port selection
        port_label = ctk.CTkLabel(config_frame, text="Serial Port:", text_color=ThemeManager.get("TEXT_MAIN"))
        port_label.pack(side="left", padx=10, pady=10)

        self.port_var = ctk.StringVar(value="/dev/ttyUSB0")
        port_entry = ctk.CTkEntry(config_frame, textvariable=self.port_var, width=150)
        port_entry.pack(side="left", padx=5)

        # ROM Size selection
        size_label = ctk.CTkLabel(config_frame, text="ROM Size (KB):", text_color=ThemeManager.get("TEXT_MAIN"))
        size_label.pack(side="left", padx=10)

        self.size_var = ctk.StringVar(value="1024")
        size_entry = ctk.CTkEntry(config_frame, textvariable=self.size_var, width=100)
        size_entry.pack(side="left", padx=5)

        # Output directory
        out_label = ctk.CTkLabel(config_frame, text="Save To:", text_color=ThemeManager.get("TEXT_MAIN"))
        out_label.pack(side="left", padx=10)

        self.out_var = ctk.StringVar(value="tunes")
        out_entry = ctk.CTkEntry(config_frame, textvariable=self.out_var, width=150)
        out_entry.pack(side="left", padx=5)

        # Control buttons frame
        button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        button_frame.pack(pady=15)

        self.btn_dump = ctk.CTkButton(
            button_frame,
            text="START DUMP",
            fg_color=ThemeManager.get("ACCENT"),
            text_color=ThemeManager.get("BACKGROUND"),
            hover_color=ThemeManager.get("ACCENT_DIM"),
            command=self.on_dump_click,
            width=150
        )
        self.btn_dump.pack(side="left", padx=10)

        self.btn_open_folder = ctk.CTkButton(
            button_frame,
            text="OPEN FOLDER",
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_MAIN"),
            command=self.on_open_folder,
            width=150
        )
        self.btn_open_folder.pack(side="left", padx=10)

        # Log output
        log_label = ctk.CTkLabel(
            self.frame,
            text="Operation Log:",
            font=("Arial", 12, "bold"),
            text_color=ThemeManager.get("TEXT_MAIN")
        )
        log_label.pack(pady=(20, 5), padx=20, anchor="w")

        self.txt_log = ctk.CTkTextbox(
            self.frame,
            width=800,
            height=300,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("TEXT_DIM"),
            font=("Consolas", 10)
        )
        self.txt_log.pack(padx=20, pady=10, fill="both", expand=True)

        self.txt_log.insert(
            "1.0",
            "Ready for tune dump operation.\n"
            "1. Connect DCAN/KLine dongle to your G37's OBD port\n"
            "2. Configure the serial port and ROM size\n"
            "3. Click START DUMP to begin ROM extraction\n\n"
            "Note: Ensure nisprog and npkern are installed and accessible in your PATH.\n"
        )

    def on_dump_click(self):
        """Start ROM dump operation."""
        port = self.port_var.get()
        try:
            rom_size = int(self.size_var.get())
        except ValueError:
            self.log("Error: ROM size must be a valid integer (KB)")
            return

        out_dir = self.out_var.get()
        if not out_dir:
            out_dir = "tunes"

        self.btn_dump.configure(state="disabled", text="DUMPING...")
        self.txt_log.delete("1.0", "end")

        from core.tune_dumper import TuneDumper

        self.dumper = TuneDumper(
            nisprog_bin="nisprog",
            port=port,
            rom_size_kb=rom_size,
            out_dir=out_dir
        )

        self.dumper.dump(
            on_log=self.log,
            on_done=self.on_dump_complete
        )

    def on_dump_complete(self, success: bool, filepath: str):
        """Called when dump completes."""
        self.btn_dump.configure(state="normal", text="START DUMP")

        if success:
            self.log(f"\n✓ SUCCESS: ROM dumped to {filepath}")
            self.log(f"File size: {os.path.getsize(filepath) / 1024:.1f} KB")
        else:
            self.log("\n✗ FAILED: ROM dump did not complete successfully.")
            self.log("Check that nisprog is installed and the dongle is properly connected.")

    def on_open_folder(self):
        """Open the output folder."""
        out_dir = self.out_var.get()
        if not out_dir:
            out_dir = "tunes"

        try:
            os.makedirs(out_dir, exist_ok=True)
            import subprocess
            import platform

            if platform.system() == "Darwin":
                subprocess.Popen(["open", out_dir])
            elif platform.system() == "Windows":
                os.startfile(out_dir)
            else:  # Linux
                subprocess.Popen(["xdg-open", out_dir])

            self.log(f"Opened folder: {os.path.abspath(out_dir)}")
        except Exception as e:
            self.log(f"Error opening folder: {e}")

    def log(self, message: str):
        """Append message to log display."""
        try:
            self.txt_log.insert("end", message + "\n")
            self.txt_log.see("end")
        except Exception:
            pass
