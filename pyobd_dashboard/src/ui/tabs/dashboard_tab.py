import customtkinter as ctk
import math
from ui.tooltip import ToolTip
from ui.theme import ThemeManager
from ui.widgets.analog_gauge import AnalogGauge

# Danger threshold for each sensor (fraction of max range where red zone starts)
DANGER_THRESHOLDS = {
    "RPM": 0.78,              # Redline at ~7000 RPM (G37 actual redline range)
    "SPEED": 1.0,             # No hard danger zone, goes to 100%
    "COOLANT_TEMP": 0.87,     # Danger at ~110°C (87% of 120 max)
    "INTAKE_TEMP": 0.75,      # Danger at high temps (cooler = better)
    "ENGINE_LOAD": 0.85,      # High load at 85%+
    "THROTTLE_POS": 1.0,      # No danger zone
    "MAF": 0.80,              # High airflow = danger zone
    "FUEL_LEVEL": 0.15,       # Red when LOW: danger zone is 0-15%
    "TIMING_ADVANCE": 0.90,   # High timing = danger
    "BAROMETRIC_PRESSURE": 1.0,  # No danger zone
    "RUN_TIME": 1.0,          # No danger zone
    "CONTROL_MODULE_VOLTAGE": 0.90,  # Danger at high voltage
    "OIL_TEMP": 0.85,         # Danger at ~110°C (overheating)
    "SHORT_FUEL_TRIM_1": 0.80,  # Danger at extreme values
    "LONG_FUEL_TRIM_1": 0.80,   # Danger at extreme values
    "FUEL_PRESSURE": 1.0,     # Depends on engine, no default danger
    "RELATIVE_THROTTLE_POS": 1.0,  # No danger zone
    "DISTANCE_W_MIL": 0.01,   # ANY distance with MIL is concerning
    "DISTANCE_SINCE_DTC_CLEAR": 1.0,  # Info only
    "ABSOLUTE_LOAD": 0.85     # High absolute load = stress
}

# Reverse metrics: danger zone is BELOW threshold, not above
REVERSE_METRICS = {"FUEL_LEVEL"}

def get_danger_threshold(sensor_name):
    """Get appropriate danger threshold for a sensor."""
    return DANGER_THRESHOLDS.get(sensor_name, 0.85)  # Default to 0.85 if unknown

class DashboardTab:
    def __init__(self, parent_frame, app_instance):
        self.frame = parent_frame
        self.app = app_instance

        self.current_page = 0
        self.items_per_page = 15
        self.total_pages = 1

        self.frame_controls = ctk.CTkFrame(self.frame, height=50, fg_color=ThemeManager.get("BACKGROUND"))
        self.frame_controls.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.frame_controls, text="Port:", font=("Arial", 12),
                     text_color=ThemeManager.get("TEXT_MAIN")).pack(side="left", padx=(10, 5))

        self.app.var_port = ctk.StringVar(value="Auto")
        self.combo_ports = ctk.CTkOptionMenu(
            self.frame_controls,
            variable=self.app.var_port,
            values=self.app.get_serial_ports(),
            width=100,
            fg_color=ThemeManager.get("CARD_BG"),
            text_color=ThemeManager.get("ACCENT"),
            button_color=ThemeManager.get("ACCENT_DIM")
        )
        self.combo_ports.pack(side="left", padx=5)

        ctk.CTkButton(self.frame_controls, text="⟳", width=30, fg_color=ThemeManager.get("CARD_BG"),
                      command=self.app.refresh_ports).pack(side="left", padx=2)

        self.app.btn_connect = ctk.CTkButton(
            self.frame_controls,
            text="CONNECT",
            fg_color=ThemeManager.get("ACCENT"),
            text_color=ThemeManager.get("BACKGROUND"),
            hover_color=ThemeManager.get("ACCENT_DIM"),
            command=self.app.on_connect_click,
            width=150
        )
        self.app.btn_connect.pack(side="left", padx=20)

        self.btn_next = ctk.CTkButton(self.frame_controls, text=">", width=40, command=self.next_page,
                                      fg_color=ThemeManager.get("CARD_BG"))
        self.btn_next.pack(side="right", padx=5)

        self.lbl_page = ctk.CTkLabel(self.frame_controls, text="Page 1/1", width=80,
                                     text_color=ThemeManager.get("TEXT_MAIN"))
        self.lbl_page.pack(side="right", padx=5)

        self.btn_prev = ctk.CTkButton(self.frame_controls, text="<", width=40, command=self.prev_page,
                                      fg_color=ThemeManager.get("CARD_BG"))
        self.btn_prev.pack(side="right", padx=5)

        self.dash_scroll = ctk.CTkScrollableFrame(self.frame, fg_color=ThemeManager.get("BACKGROUND"))
        self.dash_scroll.pack(fill="both", expand=True, padx=0, pady=0)

    def rebuild_grid(self):
        for widget in self.dash_scroll.winfo_children():
            widget.destroy()

        for cmd, state in self.app.sensor_state.items():
            state["card_widget"] = None
            state["widget_progress_bar"] = None
            state["widget_value_label"] = None

        active_sensors = [k for k, v in self.app.sensor_state.items() if v["show_var"].get()]

        total_items = len(active_sensors)
        self.total_pages = math.ceil(total_items / self.items_per_page)
        if self.total_pages < 1: self.total_pages = 1

        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)

        self.lbl_page.configure(text=f"Page {self.current_page + 1}/{self.total_pages}")

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_sensors = active_sensors[start_idx:end_idx]

        cols = 2
        for i, cmd in enumerate(page_sensors):
            row = i // cols;
            col = i % cols
            state = self.app.sensor_state[cmd]

            try:
                limit = float(state['limit_var'].get())
            except:
                limit = 100

            container = ctk.CTkFrame(self.dash_scroll, fg_color=ThemeManager.get("CARD_BG"))

            display_name = state['name']
            if len(display_name) > 18:
                display_name = display_name[:15] + "..."
            if state['unit']:
                display_name += f" ({state['unit']})"

            lbl_title = ctk.CTkLabel(
                container,
                text=display_name,
                font=("Arial", 14, "bold"),
                text_color=ThemeManager.get("TEXT_MAIN")
            )
            lbl_title.pack(pady=(10, 0))

            # Gauge and digital readout in a horizontal frame
            gauge_frame = ctk.CTkFrame(container, fg_color="transparent")
            gauge_frame.pack(pady=5)

            # Get sensor-specific danger threshold
            danger_thresh = get_danger_threshold(cmd)
            is_reverse = cmd in REVERSE_METRICS

            gauge = AnalogGauge(
                gauge_frame,
                width=180,
                height=180,
                min_val=0,
                max_val=limit,
                unit=state['unit'],
                danger_threshold=danger_thresh,
                is_reverse=is_reverse
            )
            gauge.pack(side="left", padx=5)

            # Digital readout label on the right
            digital_label = ctk.CTkLabel(
                gauge_frame,
                text="--",
                font=("Arial", 80, "bold"),
                text_color=ThemeManager.get("ACCENT")
            )
            digital_label.pack(side="left", padx=(10, 5), fill="both", expand=True)

            state["card_widget"] = container
            state["widget_progress_bar"] = gauge
            state["widget_digital_label"] = digital_label

            tooltip_text = state.get("description", state['name'])
            ToolTip(container, text=tooltip_text, delay=1000)

            container.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        self.dash_scroll.grid_columnconfigure(0, weight=1)
        self.dash_scroll.grid_columnconfigure(1, weight=1)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.rebuild_grid()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.rebuild_grid()