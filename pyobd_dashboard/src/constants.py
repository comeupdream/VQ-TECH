import os

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
PRO_PACK_DIR = os.path.join(PROJECT_ROOT, "pro_packs")

STANDARD_SENSORS = {
    "RPM": (
        "Engine RPM", "", True, True, 9000,
        "Revolutions Per Minute: How fast the engine crankshaft is spinning."
    ),
    "SPEED": (
        "Vehicle Speed", "km/h", True, True, 160,
        "Current vehicle speed as reported by the ECU."
    ),
    "COOLANT_TEMP": (
        "Coolant Temp", "°C", True, True, 120,
        "Engine Coolant Temperature: If this exceeds 110°C, the engine is overheating."
    ),
    "CONTROL_MODULE_VOLTAGE": (
        "Voltage", "V", True, False, 16,
        "ECU Voltage: Should be ~12.6V (engine off) or ~14.0V (engine running). Low voltage indicates alternator/battery issues."
    ),
    "ENGINE_LOAD": (
        "Engine Load", "%", True, False, 100,
        "Calculated Load Value: How hard the engine is working relative to its maximum capacity."
    ),
    "THROTTLE_POS": (
        "Throttle Pos", "%", True, True, 100,
        "Throttle Position: How far the gas pedal or throttle plate is open."
    ),
    "INTAKE_TEMP": (
        "Intake Air Temp", "°C", True, False, 80,
        "Intake Air Temperature (IAT): The temperature of air entering the engine. Cooler air makes more power."
    ),
    "MAF": (
        "MAF Air Flow", "g/s", True, False, 200,
        "Mass Air Flow: The exact weight of air entering the engine. Used to calculate fuel injection."
    ),
    "FUEL_LEVEL": (
        "Fuel Level", "%", True, False, 100,
        "Fuel Tank Level percentage."
    ),
    "BAROMETRIC_PRESSURE": (
        "Barometric", "kPa", True, False, 200,
        "Atmospheric Pressure: Varies based on weather and altitude."
    ),
    "TIMING_ADVANCE": (
        "Timing Adv", "°", True, False, 60,
        "Ignition Timing Advance: The angle relative to Top Dead Center (TDC) when the spark plug fires. Higher values mean earlier spark."
    ),
    "RUN_TIME": (
        "Run Time", "sec", True, False, 3600,
        "Time elapsed since the engine was started."
    ),
    "OIL_TEMP": (
        "Oil Temp", "°C", True, True, 130,
        "Engine Oil Temperature: Normal range 90-110°C. Above 120°C indicates overheating."
    ),
    "SHORT_FUEL_TRIM_1": (
        "ST Fuel Trim B1", "%", True, True, 25,
        "Short Term Fuel Trim Bank 1: ECU's real-time fuel mixture adjustment. Range -25 to +25%."
    ),
    "LONG_FUEL_TRIM_1": (
        "LT Fuel Trim B1", "%", True, True, 25,
        "Long Term Fuel Trim Bank 1: ECU's learned fuel mixture adjustment. Range -25 to +25%."
    ),
    "FUEL_PRESSURE": (
        "Fuel Pressure", "kPa", True, False, 600,
        "Fuel Rail Pressure: Normal operating pressure varies by engine. Too low = fuel starvation."
    ),
    "RELATIVE_THROTTLE_POS": (
        "Rel Throttle", "%", True, False, 100,
        "Relative Throttle Position: Current throttle angle relative to closed position."
    ),
    "DISTANCE_W_MIL": (
        "Dist w/ MIL", "km", True, False, 100,
        "Distance traveled with Malfunction Indicator Light (Check Engine) ON."
    ),
    "DISTANCE_SINCE_DTC_CLEAR": (
        "Dist Since Clear", "km", True, False, 1000,
        "Distance traveled since Diagnostic Trouble Codes were last cleared."
    ),
    "ABSOLUTE_LOAD": (
        "Absolute Load", "%", True, False, 100,
        "Absolute Engine Load: Percentage of max possible engine load."
    )
}

HIGH_PRIORITY_SENSORS = [
    "RPM",
    "SPEED",
    "THROTTLE_POS",
    "ENGINE_LOAD",
    "CONTROL_MODULE_VOLTAGE",

    "BMW_BOOST_PRESSURE",
    "BMW_RAIL_PRESSURE",
    "F150L_HV_BATTERY_CURRENT",
    "VW_HV_BATTERY_CURRENT"
]