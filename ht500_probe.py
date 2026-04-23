"""
Raw HT500 probe — bypasses python-obd so we can see exactly what the
ELM327 is (or isn't) saying at each baud rate.

Just run:  python ht500_probe.py

It opens COM3, sweeps common ELM327 baud rates, sends ATZ + ATI, and
prints the raw bytes that come back. Whichever baud returns something
that looks like 'ELM327 v...' is the right one to pass to obd.OBD().
"""
import time
import serial

PORT = "COM3"
BAUDS = [38400, 9600, 115200, 57600, 500000]


def drain(ser, t=0.25):
    end = time.time() + t
    buf = bytearray()
    while time.time() < end:
        n = ser.in_waiting
        if n:
            buf += ser.read(n)
            end = time.time() + t
        else:
            time.sleep(0.02)
    return bytes(buf)


def send(ser, cmd, wait=1.5):
    ser.reset_input_buffer()
    ser.write((cmd + "\r").encode())
    ser.flush()
    time.sleep(0.05)
    end = time.time() + wait
    buf = bytearray()
    while time.time() < end:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            buf += chunk
            if b">" in chunk:
                break
        else:
            time.sleep(0.02)
    return bytes(buf)


def try_baud(baud):
    print(f"\n=== {PORT} @ {baud} ===")
    try:
        ser = serial.Serial(PORT, baud, timeout=0.2, write_timeout=1.0)
    except Exception as e:
        print(f"  open failed: {e}")
        return False

    try:
        time.sleep(0.4)
        junk = drain(ser, 0.3)
        if junk:
            print(f"  boot noise: {junk!r}")

        for cmd in ("ATZ", "ATE0", "ATI", "ATRV", "ATDP"):
            resp = send(ser, cmd, wait=2.0 if cmd == "ATZ" else 1.0)
            print(f"  -> {cmd:<5}  <- {resp!r}")
            if cmd == "ATI" and b"ELM" in resp:
                print(f"  *** ELM RESPONDING AT {baud} ***")
                return True
        return False
    finally:
        try:
            ser.close()
        except Exception:
            pass


def main():
    print(f"Probing HT500 on {PORT}.")
    print("Key the car ON (engine running is best), "
          "wait ~5 s after the dash lights come up, then run this.\n")
    for b in BAUDS:
        if try_baud(b):
            print(f"\n>>> SUCCESS: set baudrate={b} in g37_dashboard.py")
            return
        time.sleep(0.5)
    print("\nNo baud rate returned ELM output.")
    print("Unplug the HT500 for 10 s, reseat it, make sure the engine is")
    print("running (not just ACC), and run this script again.")


if __name__ == "__main__":
    main()
