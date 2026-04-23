import obd
import time

# Enable debug so we can see exactly what's happening
obd.logger.setLevel(obd.logging.DEBUG)

print("Attempting to connect to HT500 on COM3...")

# Correct connection syntax for your version
connection = obd.OBD(
    "COM3",               # positional port - this is the fix
    baudrate=38400,
    fast=False,
    timeout=0.2
)

if not connection.is_connected():
    print("❌ Still could not connect.")
    print("Try these next:")
    print("1. Car ignition FULLY ON (dash lights lit)")
    print("2. Unplug the HT500 and plug it back in firmly")
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
