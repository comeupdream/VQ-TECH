from obd_handler import OBDHandler
from ui.main_window import DashboardApp
from splash_screen import show_splash

SIMULATION_MODE = False

if __name__ == "__main__":
    # Show custom VQ-TECH startup splash screen
    show_splash(duration=2500)

    # Launch main dashboard
    handler = OBDHandler(simulation=SIMULATION_MODE)
    app = DashboardApp(handler)
    app.mainloop()
