"""
Minimal live monitor for the G37 via HT500 (ELM327 v1.3a clone) on COM3.

Key facts learned from ht500_probe.py:
  - HT500 talks at 38400 baud.
  - It identifies as ELM327 v1.3a (clone firmware) — Mode 01 works,
    Mode 22 extended PIDs are unreliable on this chip.
  - ATZ reset takes ~1.5 s, so python-obd needs a generous timeout or
    it bails mid-handshake.
"""
import obd
import time

obd.logger.setLevel(obd.logging.INFO)

PORT = "COM3"
BAUD = 38400

print(f"Connecting to HT500 on {PORT} @ {BAUD}...")

connection = obd.OBD(
    PORT,
    baudrate=BAUD,
    protocol="6",    # force ISO 15765-4 CAN 11-bit 500k (G37's bus)
    fast=False,      # don't send tailing hack char (BT-friendly)
    timeout=1.0,     # v1.3a clones need >= 1.0 s or ATZ times out
    check_voltage=False,
)

if not connection.is_connected():
    print("❌ Still could not connect.")
    print("- Engine ON (not just ACC).")
    print("- HT500 light solid (not blinking fast).")
    print("- COM3 not held by another app (FORScan, Torque, etc.).")
    raise SystemExit(1)

print(f"✅ Connected. Protocol: {connection.protocol_name()}")
print("Streaming. Ctrl+C to stop.\n")

CMDS = [
    ("RPM",      obd.commands.RPM),
    ("SPEED",    obd.commands.SPEED),
    ("COOLANT",  obd.commands.COOLANT_TEMP),
    ("INTAKE_T", obd.commands.INTAKE_TEMP),
    ("THROTTLE", obd.commands.THROTTLE_POS),
    ("MAF",      obd.commands.MAF),
    ("TIMING",   obd.commands.TIMING_ADVANCE),
    ("STFT_B1",  obd.commands.SHORT_FUEL_TRIM_1),
    ("LTFT_B1",  obd.commands.LONG_FUEL_TRIM_1),
    ("STFT_B2",  obd.commands.SHORT_FUEL_TRIM_2),
    ("LTFT_B2",  obd.commands.LONG_FUEL_TRIM_2),
    ("LOAD",     obd.commands.ENGINE_LOAD),
]

try:
    while True:
        parts = []
        for label, cmd in CMDS:
            r = connection.query(cmd, force=True)
            v = "--" if r is None or r.is_null() else r.value
            parts.append(f"{label}:{v}")
        print(" | ".join(parts))
        time.sleep(0.25)
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    connection.close()
