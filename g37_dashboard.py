import obd
import time

obd.logger.setLevel(obd.logging.DEBUG)

print("Attempting to connect to HT500 on COM3 (9600 baud + CAN)...")

connection = obd.OBD(
    "COM3",           # your COM port
    baudrate=9600,    # most reliable for v1.3a Bluetooth
    protocol=6,       # high-speed CAN (what your G37 uses)
    fast=False,
    timeout=1.0
)

if not connection.is_connected():
    print("❌ Still could not connect.")
    print("\nTry these right now:")
    print("1. START THE ENGINE (not just ignition ON — many G37s need the ECU fully awake)")
    print("2. Unplug the HT500 → wait 5 seconds → plug it back in firmly")
    print("3. Restart the script")
    exit()

print("✅ Connected to G37! Live data streaming...\n")

while True:
    rpm = connection.query(obd.commands.RPM)
    coolant = connection.query(obd.commands.COOLANT_TEMP)
    throttle = connection.query(obd.commands.THROTTLE_POS)

    print(f"RPM: {rpm.value} | Coolant: {coolant.value} | Throttle: {throttle.value}")

    time.sleep(0.2)
