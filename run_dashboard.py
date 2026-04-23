"""
Launch PyOBD Professional Dashboard with analog gauges.

This is Paul-HenryP's PyOBD-Dashboard fork — a modern gauge-based OBD-II diagnostic
tool with real-time analog displays, performance dyno mode, live graphing, and themes.

Run with --demo flag for demo mode (no car needed).

Usage:
    python run_dashboard.py           # Normal mode, connect to car
    python run_dashboard.py --demo    # Demo mode with simulated data
"""
import os
import sys
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(HERE, "pyobd_dashboard")

if not os.path.isdir(DASHBOARD):
    print("pyobd_dashboard/ is missing. Did you `git pull`?", file=sys.stderr)
    sys.exit(1)

os.chdir(DASHBOARD)
sys.path.insert(0, os.path.join(DASHBOARD, "src"))

# Pass through command-line arguments (e.g., --demo)
runpy.run_path(os.path.join(DASHBOARD, "src", "main.py"), run_name="__main__")
