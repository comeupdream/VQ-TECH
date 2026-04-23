import obd
import time

# Connect to your HT500 on COM4
connection = obd.OBD("COM4")   # <-- this is the key line

if not connection.is_connected():
    print("❌ Could not connect - double-check dongle is plugged in and car is ON")
    exit()

print("✅ Connected to G37! Live data streaming...\n")

# Simple live loop - press Ctrl+C to stop
while True:
    # Standard PIDs (always work)
    rpm = connection.query(obd.commands.RPM)
    coolant = connection.query(obd.commands.COOLANT_TEMP)
    throttle = connection.query(obd.commands.THROTTLE_POS)

    print(f"RPM: {rpm.value} | Coolant: {coolant.value} | Throttle: {throttle.value}")

    # Example G37 Mode 22 extended PID (bank 1 AFR - add more below)
    # You can add any Mode 22 command here once we confirm it works
    time.sleep(0.2)   # updates ~5 times per second
