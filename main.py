"""
VQ-TECH — Real-time ECU monitoring dashboard for the Infiniti G37 Sport
(VQ37VHR).

Live gauges / graphs / CSV datalogging via an ELM327 Bluetooth dongle,
plus a future-ready 'Dump Current Tune' button that shells out to
nisprog + npkern over the K+DCAN USB cable.

Run examples:
    python main.py --demo                              # offline demo
    python main.py --port /dev/rfcomm0                 # paired BT ELM327
    python main.py --port COM5 --baud 38400            # Windows
"""
import argparse
import sys

from core.obd_client import OBDClient
from ui.dashboard import Dashboard


def parse_args():
    p = argparse.ArgumentParser(description="VQ-TECH G37 ECU dashboard")
    p.add_argument("--port", default=None,
                   help="ELM327 serial port (e.g. /dev/rfcomm0, COM5). "
                        "If omitted, python-obd auto-discovers.")
    p.add_argument("--baud", type=int, default=38400,
                   help="Baud rate (default 38400 for ELM327 BT).")
    p.add_argument("--demo", action="store_true",
                   help="Run with simulated data (no OBD required).")
    p.add_argument("--poll-hz", type=float, default=10.0,
                   help="Background OBD poll rate in Hz (default 10).")
    return p.parse_args()


def main():
    args = parse_args()

    client = OBDClient(port=args.port, baudrate=args.baud, demo=args.demo)
    if not client.connect():
        print("ERROR: could not connect to ELM327. "
              "Pair the dongle / bind rfcomm, or re-run with --demo.",
              file=sys.stderr)
        sys.exit(1)

    client.start(interval=1.0 / args.poll_hz)

    try:
        dash = Dashboard(client)
        dash.build()
        dash.run()
    except KeyboardInterrupt:
        pass
    finally:
        client.stop()


if __name__ == "__main__":
    main()
