import obd
import time

# Enable debug so we can see exactly what's happening
obd.logger.setLevel(obd.logging.DEBUG)

print("Attempting to connect to HT500 on COM3...")

# Force the correct Bluetooth-friendly settings
connection = obd.OBD(
    port="COM3",          # <-- changed to COM3
    baudrate=38400,       # most reliable for Bluetooth ELM327
    protocol=None,        # let it auto-detect
    fast=False,           # important for Bluetooth stability
    timeout=0.2           # give it a little more time
)

if not connection.is_connected():
    print("❌ Still could not connect.")
    print("Try these next:")
    print("1. Make sure car ignition is fully ON (dash lights on)")
    print("2. Unplug/replug the HT500 firmly")
    print("3. Restart the script")
    exit()

print("✅ Connected to G37! Live data streaming...\n")

# Live loop
while True:
    rpm = connection.query(obd.commands.RPM)
    coolant = connection.query(obd.commands.COOLANT_TEMP)
    throttle = connection.query(obd.commands.THROTTLE_POS)

    print(f"RPM: {rpm.value} | Coolant: {coolant.value} | Throttle: {throttle.value}")

    time.sleep(0.2)
