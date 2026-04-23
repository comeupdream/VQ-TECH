import obd
from obd import OBDCommand
from obd.utils import bytes_to_int
import random
import time
import re
import math

class OBDHandler:
    def __init__(self, simulation=False, log_callback=None):
        self.simulation = simulation
        self.connection = None
        self.status = "Disconnected"
        self.log_callback = log_callback
        self.inter_command_delay = 0.01

        self.pro_defs = {}
        self.supported_commands = set()

        self.sim_start_time = time.time()
        self.sim_speed = 0

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        print(message)

    def set_pro_definitions(self, defs):
        self.pro_defs = defs

    def is_connected(self):
        return self.status == "Connected" or self.status == "Connected (SIMULATION)"

    def connect(self, port_name=None):
        if self.simulation:
            self.log("Attempting connection (SIMULATION)...")
            self.status = "Connected (SIMULATION)"
            self.sim_start_time = time.time()
            self.log("SUCCESS: Simulation Mode Active")
            return True

        self.log(f"Attempting connection to {port_name if port_name else 'Auto-Scan'}...")

        try:
            if port_name and port_name != "Auto":
                self.connection = obd.OBD(portstr=port_name, fast=False, timeout=30)
            else:
                self.connection = obd.OBD(fast=False, timeout=30)

            if self.connection.is_connected():
                self.status = "Connected"
                self.log(f"SUCCESS: Connected to {self.connection.port_name}")
                self.log(f"Protocol: {self.connection.protocol_name()}")

                self.supported_commands = self.connection.supported_commands
                self.log(f"Auto-Detected {len(self.supported_commands)} supported sensors.")
                return True
            else:
                self.status = "Failed"
                self.log("ERROR: Interface found, but no connection to ECU.")
                return False
        except Exception as e:
            self.status = "Error"
            self.log(f"CRITICAL ERROR: {e}")
            return False

    def disconnect(self):
        self.log("Disconnecting...")
        if self.connection:
            self.connection.close()
            self.connection = None
        self.status = "Disconnected"
        self.supported_commands = set()
        self.log("Disconnected.")

    def check_supported(self, command_key):
        if self.simulation: return True
        if not self.is_connected(): return False

        if hasattr(obd.commands, command_key):
            cmd = getattr(obd.commands, command_key)
            return cmd in self.supported_commands

        if command_key in self.pro_defs:
            return True

        return False

    def _set_header(self, header_hex):
        if not header_hex: return
        try:
            cmd = OBDCommand("SET_HEADER", "AT SH " + header_hex, b"", lambda m: m)
            self.connection.query(cmd, force=True)
        except Exception:
            pass

    def query_sensor(self, command_key):
        if not self.is_connected(): return None
        if self.simulation: return self._simulate_data(command_key)

        if hasattr(obd.commands, command_key):
            cmd = getattr(obd.commands, command_key)

            if cmd not in self.supported_commands:
                return None

            time.sleep(self.inter_command_delay)
            try:
                response = self.connection.query(cmd)
                if response.is_null(): return None

                val = response.value.magnitude
                if isinstance(val, float):
                    return round(val, 2)
                return val
            except:
                return None

        elif command_key in self.pro_defs:
            return self._query_custom_pid(command_key)

        return None

    def _query_custom_pid(self, key):
        definition = self.pro_defs[key]
        if len(definition) < 8: return None

        pid_hex = definition[5]
        header_hex = definition[6]
        formula = definition[7]

        time.sleep(self.inter_command_delay)

        try:
            if header_hex:
                self._set_header(header_hex)

            mode = pid_hex[:2]
            pid = pid_hex[2:]

            cmd = OBDCommand("CUSTOM_PID", mode + pid, b"", lambda m: m)
            raw_response = self.connection.query(cmd, force=True)

            if raw_response.is_null(): return None
            if not raw_response.messages: return None
            data_bytes = raw_response.messages[0].data

            return self._calculate_formula(formula, data_bytes)

        except Exception as e:
            return None

    def _calculate_formula(self, formula, data_bytes):
        variables = {}
        for i, byte_val in enumerate(data_bytes):
            char_code = 65 + i
            if char_code > 90: break
            variables[chr(char_code)] = byte_val

        try:
            allowed_names = {"min": min, "max": max, "abs": abs, "signed": self._signed}
            allowed_names.update(variables)
            result = eval(formula, {"__builtins__": {}}, allowed_names)
            return float(result)
        except:
            return None

    def _signed(self, val):
        if val > 127: return val - 256
        return val

    def _decode_uds_dtc(self, byte1, byte2, byte3):
        """Converts 3-byte UDS hex to standard P/U/B/C code"""

        type_bits = (byte1 & 0xC0) >> 6
        prefix = {0: "P", 1: "C", 2: "B", 3: "U"}[type_bits]

        second_char = (byte1 & 0x30) >> 4

        rest_of_byte1 = byte1 & 0x0F

        hex_code = f"{prefix}{second_char}{rest_of_byte1:X}{byte2:02X}{byte3:02X}"
        return hex_code.upper()

    def _get_uds_dtcs(self, target_header="7E0"):
        """EXPERIMENTAL: Scan for UDS Service 19 faults"""
        codes = []
        try:
            self.log(f"Attempting UDS (Service 19) Scan on {target_header}...")
            self._set_header(target_header)
            time.sleep(0.1)

            cmd = OBDCommand("UDS_SCAN", "19 02 FF", b"", lambda m: m)
            response = self.connection.query(cmd, force=True)

            if not response.is_null() and response.messages:
                data = response.messages[0].data

                if len(data) > 0 and data[0] == 0x59:
                    self.log(f"UDS RAW DATA: {data.hex()}")

                    i = 3
                    while i + 3 < len(data):
                        b1 = data[i]
                        b2 = data[i + 1]
                        b3 = data[i + 2]
                        status = data[i + 3]

                        if status & 0x09:  # 0x01 (Current) or 0x08 (Confirmed)
                            code_str = self._decode_uds_dtc(b1, b2, b3)
                            codes.append((code_str, f"UDS Extended (Status: {status:02X})"))

                        i += 4
                elif len(data) > 0 and data[0] == 0x7F:
                    self.log(f"UDS Not Supported by this module (Response: {data.hex()})")
            else:
                self.log("No response to UDS Scan.")

        except Exception as e:
            self.log(f"UDS Logic Error: {e}")

        return codes

    def get_dtc(self):
        if not self.is_connected(): return {}
        self.log("Starting Deep DTC Scan...")

        dtc_groups = {
            "ENGINE - CONFIRMED": [],
            "ENGINE - PENDING": [],
            "UDS / EXTENDED (Experimental)": [],

            "TRANSMISSION": []
        }

        if self.simulation:
            return {"ENGINE - CONFIRMED": [("P0300", "Random Misfire")]}

        try:

            self.log("Scanning Engine (Standard)...")
            self._set_header("7E0")

            res_conf = self.connection.query(obd.commands.GET_DTC, force=True)
            if not res_conf.is_null() and res_conf.value:
                for c in res_conf.value: dtc_groups["ENGINE - CONFIRMED"].append(c)

            res_pend = self.connection.query(obd.commands.GET_CURRENT_DTC, force=True)
            if not res_pend.is_null() and res_pend.value:
                for c in res_pend.value: dtc_groups["ENGINE - PENDING"].append(c)

            uds_codes = self._get_uds_dtcs("7E0")
            for c in uds_codes:

                is_duplicate = any(existing[0] == c[0] for existing in dtc_groups["ENGINE - CONFIRMED"])
                if not is_duplicate:
                    dtc_groups["UDS / EXTENDED (Experimental)"].append(c)

            self.log("Scanning Trans (Standard)...")
            self._set_header("7E1")
            res_tcu = self.connection.query(obd.commands.GET_DTC, force=True)
            if not res_tcu.is_null() and res_tcu.value:
                for c in res_tcu.value: dtc_groups["TRANSMISSION"].append(c)

        except Exception as e:
            self.log(f"Scan Critical Error: {e}")
        finally:
            self._set_header("7E0")

        self.log("Scan Complete.")
        return dtc_groups

    def get_freeze_frame_snapshot(self, sensor_list):
        self.log("Reading Freeze Frame Data...")
        snapshot = {}
        if self.simulation:
            for name in sensor_list: snapshot[name] = self._simulate_data(name)
            return snapshot

        if self.connection and self.connection.is_connected():
            for name in sensor_list:
                val = self.query_sensor(name)
                if val is not None:
                    snapshot[name] = val
        return snapshot

    def clear_dtc(self):
        self.log("Attempting to Clear DTCs...")
        if self.simulation:
            time.sleep(1)
            return True

        if self.connection and self.connection.is_connected():
            try:

                self._set_header("7E0")
                self.connection.query(obd.commands.CLEAR_DTC)

                self._set_header("7E1")
                self.connection.query(obd.commands.CLEAR_DTC)
                self._set_header("7E0")
                self.log("Command Sent: CLEAR_DTC")
                return True
            except Exception as e:
                self.log(f"Clear Failed: {e}")
                return False
        return False

    def _simulate_data(self, name):
        """Realistic engine simulation with smooth, correlated sensor values."""
        elapsed = time.time() - self.sim_start_time

        # Initialize persistent sim state if needed
        if not hasattr(self, '_sim_state'):
            self._sim_state = {
                'rpm': 800,
                'speed': 0,
                'throttle': 0,
                'coolant_temp': 20,
                'fuel_level': 100,
                'last_update': elapsed
            }

        # Update simulation state
        state = self._sim_state
        dt = min(elapsed - state['last_update'], 0.2)  # Cap delta time
        state['last_update'] = elapsed

        # Realistic throttle input (varies over time)
        throttle_target = 10 + 70 * (0.5 + 0.5 * math.sin(elapsed / 5))
        throttle_target += random.gauss(0, 5)
        state['throttle'] = 0.9 * state['throttle'] + 0.1 * throttle_target
        state['throttle'] = max(0, min(100, state['throttle']))

        # RPM based on throttle (with inertia)
        rpm_from_throttle = 800 + state['throttle'] * 65  # 800-6500 RPM range
        rpm_acceleration = 2000 * (rpm_from_throttle - state['rpm']) / max(1, abs(rpm_from_throttle - state['rpm']) + 100)
        state['rpm'] += rpm_acceleration * dt
        state['rpm'] = max(700, min(7200, state['rpm']))

        # Speed correlates with RPM (roughly 1 km/h per 50 RPM after idle)
        speed_target = max(0, (state['rpm'] - 800) / 50)
        state['speed'] = 0.85 * state['speed'] + 0.15 * speed_target
        state['speed'] = max(0, min(200, state['speed']))

        # Coolant temp gradually warms up
        coolant_target = 85 + 15 * (state['rpm'] / 7200)  # 85-100°C depending on load
        state['coolant_temp'] += (coolant_target - state['coolant_temp']) * 0.01 * dt
        state['coolant_temp'] = max(20, min(110, state['coolant_temp']))

        # Fuel consumption (0.1 L per hour at cruise, more under load)
        fuel_burn_rate = 0.1 + 0.3 * (state['throttle'] / 100)
        state['fuel_level'] -= fuel_burn_rate * dt / 3600
        state['fuel_level'] = max(0, min(100, state['fuel_level']))

        # Return sensor values based on current state
        if name == 'RUN_TIME':
            return int(elapsed)
        elif name == 'RPM':
            return int(state['rpm'])
        elif name == 'SPEED':
            return round(state['speed'], 1)
        elif name == 'THROTTLE_POS':
            return round(state['throttle'], 1)
        elif name == 'COOLANT_TEMP':
            return round(state['coolant_temp'], 1)
        elif name == 'INTAKE_TEMP':
            # Intake temp follows coolant with some variation
            intake_base = state['coolant_temp'] - 30
            return round(max(10, intake_base + random.gauss(0, 2)), 1)
        elif name == 'ENGINE_LOAD':
            # Load correlates with throttle and RPM
            return round(state['throttle'] * (0.5 + 0.5 * state['rpm'] / 7200), 1)
        elif name == 'TIMING_ADVANCE':
            return round(8 + 15 * (state['rpm'] / 7200), 1)
        elif name == 'FUEL_LEVEL':
            return round(state['fuel_level'], 1)
        elif name == 'MAF':
            # MAF (Mass Air Flow) correlates with throttle and RPM
            return round(3 + state['throttle'] * 0.4 + random.gauss(0, 0.5), 2)
        elif name == 'CONTROL_MODULE_VOLTAGE':
            # Battery voltage - roughly stable, slight ripple
            return round(13.8 + 0.4 * random.random(), 2)
        elif name == 'BAROMETRIC_PRESSURE':
            return round(101.3 + random.gauss(0, 0.5), 1)
        elif name == 'OIL_TEMP':
            # Oil temp follows coolant but lags slightly (hotter)
            oil_temp = state['coolant_temp'] + 5 + random.gauss(0, 1)
            return round(max(20, oil_temp), 1)
        elif name == 'SHORT_FUEL_TRIM_1':
            # STFT oscillates around 0, -10 to +10 typical
            return round(random.gauss(0, 3), 1)
        elif name == 'LONG_FUEL_TRIM_1':
            # LTFT is more stable, learned over time
            return round(random.gauss(2, 1), 1)
        elif name == 'FUEL_PRESSURE':
            # Fuel pressure stable when running
            return round(350 + random.gauss(0, 10), 1)
        elif name == 'RELATIVE_THROTTLE_POS':
            # Relative throttle tracks absolute throttle
            return round(state['throttle'], 1)
        elif name == 'DISTANCE_W_MIL':
            return 0  # No check engine in demo
        elif name == 'DISTANCE_SINCE_DTC_CLEAR':
            # Simulate some distance since last clear
            return int(elapsed * 0.01)  # slow accumulator
        elif name == 'ABSOLUTE_LOAD':
            # Absolute load similar to engine load
            return round(state['throttle'] * 0.8 + random.gauss(0, 2), 1)
        else:
            # Default: return value in expected range based on name
            return round(random.uniform(0, 100), 1)