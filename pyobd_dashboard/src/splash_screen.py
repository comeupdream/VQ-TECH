"""Custom startup splash screen for VQ-TECH PyOBD Dashboard."""
import customtkinter as ctk
import tkinter as tk
from version import get_version_string


def show_splash(duration=2500):
    """Display splash screen for specified duration (ms), then close and return.

    This is a blocking call - it shows the splash until duration expires.
    """
    splash = ctk.CTk()
    splash.title("VQ-TECH")

    # Configure window
    width, height = 600, 400
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")

    # Remove window decorations
    splash.overrideredirect(True)

    # Dark background with cyber theme
    bg_color = "#0a0f1a"
    accent_color = "#00ffff"
    text_color = "#ffffff"

    splash.configure(fg_color=bg_color)

    # Main container with border effect
    border_frame = ctk.CTkFrame(
        splash,
        fg_color=bg_color,
        border_color=accent_color,
        border_width=3,
        corner_radius=0
    )
    border_frame.pack(fill="both", expand=True, padx=2, pady=2)

    # VQ-TECH Title (large)
    title_label = ctk.CTkLabel(
        border_frame,
        text="VQ-TECH",
        font=("Arial", 64, "bold"),
        text_color=accent_color
    )
    title_label.pack(pady=(50, 10))

    # Subtitle
    subtitle_label = ctk.CTkLabel(
        border_frame,
        text="INFINITI G37 SPORT  |  VQ37VHR",
        font=("Arial", 18, "bold"),
        text_color=text_color
    )
    subtitle_label.pack(pady=(0, 5))

    # Tagline
    tagline_label = ctk.CTkLabel(
        border_frame,
        text="Real-Time ECU Monitoring Dashboard",
        font=("Arial", 12),
        text_color="#888888"
    )
    tagline_label.pack(pady=(0, 30))

    # Accent separator line effect
    separator = ctk.CTkFrame(border_frame, height=2, width=400, fg_color=accent_color)
    separator.pack(pady=5)

    # Version
    version_label = ctk.CTkLabel(
        border_frame,
        text=get_version_string(),
        font=("Arial", 11, "bold"),
        text_color=accent_color
    )
    version_label.pack(pady=(15, 10))

    # Loading indicator
    loading_label = ctk.CTkLabel(
        border_frame,
        text="INITIALIZING...",
        font=("Arial", 10),
        text_color="#666666"
    )
    loading_label.pack(pady=(10, 5))

    # Progress bar
    progress = ctk.CTkProgressBar(
        border_frame,
        width=400,
        height=6,
        progress_color=accent_color,
        fg_color="#1a2030"
    )
    progress.pack(pady=(0, 20))
    progress.set(0)

    # Animate progress
    steps = 40
    interval = duration // steps

    def update_progress(step=0):
        if step <= steps:
            try:
                progress.set(step / steps)
                messages = ["INITIALIZING...", "LOADING SENSORS...", "CALIBRATING GAUGES...",
                            "APPLYING THEME...", "READY..."]
                msg_idx = min(step * len(messages) // steps, len(messages) - 1)
                loading_label.configure(text=messages[msg_idx])
                splash.after(interval, lambda: update_progress(step + 1))
            except Exception:
                pass

    update_progress()

    # Auto-close after duration
    splash.after(duration, splash.destroy)

    # Run the splash event loop
    splash.mainloop()
