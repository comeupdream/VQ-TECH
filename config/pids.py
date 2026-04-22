"""
PID definitions for the VQ37VHR (Infiniti G37 Sport, 2008-2013).

- STANDARD_PIDS: OBD-II Mode 01 commands available on any ECU.
- EXTENDED_PIDS: Nissan Mode 22 PIDs for VVEL, knock, per-bank data, etc.

Extended PID values here are the common community-reported VQ37VHR Mode 22
addresses. Verify against NissanDefinitions / ECUFlash XMLs for your exact
ECU part number before datalogging production runs.
"""
import obd
from obd import OBDCommand, Unit
from obd.protocols import ECU
from obd.decoders import raw_string


STANDARD_PIDS = {
    "RPM":              obd.commands.RPM,
    "SPEED":            obd.commands.SPEED,
    "THROTTLE":         obd.commands.THROTTLE_POS,
    "COOLANT":          obd.commands.COOLANT_TEMP,
    "INTAKE_TEMP":      obd.commands.INTAKE_TEMP,
    "MAF":              obd.commands.MAF,
    "TIMING_ADV":       obd.commands.TIMING_ADVANCE,
    "STFT_B1":          obd.commands.SHORT_FUEL_TRIM_1,
    "LTFT_B1":          obd.commands.LONG_FUEL_TRIM_1,
    "STFT_B2":          obd.commands.SHORT_FUEL_TRIM_2,
    "LTFT_B2":          obd.commands.LONG_FUEL_TRIM_2,
    "O2_B1S1":          obd.commands.O2_B1S1,
    "O2_B2S1":          obd.commands.O2_B2S1,
    "LOAD":             obd.commands.ENGINE_LOAD,
    "MAP":              obd.commands.INTAKE_PRESSURE,
    "FUEL_PRESSURE":    obd.commands.FUEL_PRESSURE,
}


def _decode_percent(messages):
    """Signed percent helper (STFT/trim style)."""
    data = messages[0].data[2:]
    if not data:
        return None
    return ((data[0] - 128) * 100.0 / 128.0) * Unit.percent


def _decode_u16_scaled(scale=1.0, offset=0.0, unit=Unit.ratio):
    def _d(messages):
        data = messages[0].data[2:]
        if len(data) < 2:
            return None
        raw = (data[0] << 8) | data[1]
        return (raw * scale + offset) * unit
    return _d


def _decode_s8_scaled(scale=1.0, offset=0.0, unit=Unit.degree):
    def _d(messages):
        data = messages[0].data[2:]
        if not data:
            return None
        raw = data[0]
        if raw > 127:
            raw -= 256
        return (raw * scale + offset) * unit
    return _d


def _mk(name, pid_hex, decoder, bytes_=3, unit_label=""):
    """Build a Mode 22 extended command."""
    pid = bytes.fromhex(pid_hex)
    cmd = OBDCommand(
        name,
        name,
        b"22" + pid.hex().upper().encode(),
        bytes_,
        decoder,
        ECU.ENGINE,
        True,
    )
    cmd.unit_label = unit_label
    return cmd


EXTENDED_PIDS = {
    "AFR_B1":        _mk("AFR_B1",       "1103", _decode_u16_scaled(0.0001526, unit=Unit.ratio), 4, "lambda"),
    "AFR_B2":        _mk("AFR_B2",       "1104", _decode_u16_scaled(0.0001526, unit=Unit.ratio), 4, "lambda"),
    "KNOCK_CORR":    _mk("KNOCK_CORR",   "1161", _decode_s8_scaled(0.375), 3, "deg"),
    "VVEL_B1":       _mk("VVEL_B1",      "1180", _decode_u16_scaled(0.01, unit=Unit.degree), 4, "deg"),
    "VVEL_B2":       _mk("VVEL_B2",      "1181", _decode_u16_scaled(0.01, unit=Unit.degree), 4, "deg"),
    "CAM_ADV_B1":    _mk("CAM_ADV_B1",   "1190", _decode_s8_scaled(0.5), 3, "deg"),
    "CAM_ADV_B2":    _mk("CAM_ADV_B2",   "1191", _decode_s8_scaled(0.5), 3, "deg"),
    "INJ_PW_B1":     _mk("INJ_PW_B1",    "1120", _decode_u16_scaled(0.004, unit=Unit.millisecond), 4, "ms"),
    "INJ_PW_B2":     _mk("INJ_PW_B2",    "1121", _decode_u16_scaled(0.004, unit=Unit.millisecond), 4, "ms"),
    "OIL_TEMP":      _mk("OIL_TEMP",     "1155", _decode_s8_scaled(1.0, -40.0, Unit.celsius), 3, "C"),
    "BATT_V":        _mk("BATT_V",       "110D", _decode_u16_scaled(0.01, unit=Unit.volt), 4, "V"),
    "MAF_V":         _mk("MAF_V",        "1148", _decode_u16_scaled(0.005, unit=Unit.volt), 4, "V"),
}


GAUGE_LAYOUT = [
    ("RPM",        "RPM",         0, 8000,  6500, "rpm"),
    ("SPEED",      "SPEED",       0, 260,   999,  "km/h"),
    ("THROTTLE",   "THROTTLE",    0, 100,   95,   "%"),
    ("AFR_B1",     "AFR_B1",      0.70, 1.30, 0.85, "λ"),
    ("AFR_B2",     "AFR_B2",      0.70, 1.30, 0.85, "λ"),
    ("TIMING_ADV", "TIMING",      -10, 50,   45,   "°"),
    ("KNOCK_CORR", "KNOCK CORR",  -15, 5,    -6,   "°"),
    ("VVEL_B1",    "VVEL B1",     0, 60,    999,  "°"),
    ("VVEL_B2",    "VVEL B2",     0, 60,    999,  "°"),
    ("COOLANT",    "COOLANT",     40, 130,  108,  "°C"),
    ("OIL_TEMP",   "OIL",         40, 140,  120,  "°C"),
    ("MAF_V",      "MAF",         0, 5,     999,  "V"),
    ("INJ_PW_B1",  "INJ PW",      0, 20,    999,  "ms"),
    ("LTFT_B1",    "LTFT B1",     -25, 25,  15,   "%"),
    ("LTFT_B2",    "LTFT B2",     -25, 25,  15,   "%"),
    ("BATT_V",     "BATTERY",     10, 16,   999,  "V"),
]
