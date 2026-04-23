# VQ-TECH

Real-time ECU monitoring dashboard for the **Infiniti G37 Sport (VQ37VHR)**.

- Live polished gauges — RPM, bank AFRs, ignition timing, VVEL lift/cam
  angles, knock correction, fuel trims, oil/coolant/intake temps,
  MAF voltage, throttle %, injector pulse width, battery.
- Multi-graph live view with rolling 30 s window.
- CSV datalogging (every snapshot, background thread).
- Dark/cyber theme, tab-based layout.
- **Future:** one-click ROM dump via `nisprog` + `npkern` over K+DCAN.

Stack: **python-obd** + **Dear PyGui**.

---

## Project structure

```
VQ-TECH/
├── main.py                  # entry point
├── requirements.txt
├── README.md
├── config/
│   ├── theme.py             # dark/cyber colors + DPG theme
│   └── pids.py              # standard + G37 Mode 22 extended PIDs
├── core/
│   ├── obd_client.py        # python-obd wrapper + demo simulator
│   ├── datalogger.py        # CSV writer (background thread)
│   └── tune_dumper.py       # nisprog subprocess wrapper (future)
├── ui/
│   ├── gauges.py            # arc gauge widget (DPG drawlist)
│   ├── graphs.py            # rolling live plot
│   └── dashboard.py         # tabbed layout + controls
├── logs/                    # CSV output
└── tunes/                   # ROM dumps (.bin)
```

---

## Setup

### 1. Python deps

```bash
cd VQ-TECH
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pair the ELM327 Bluetooth dongle

**Linux**
```bash
sudo bluetoothctl
# scan on, pair <MAC>, trust <MAC>, quit
sudo rfcomm bind 0 <MAC> 1     # creates /dev/rfcomm0
```

**Windows** — pair in Bluetooth settings, note the outgoing COM port
(e.g. `COM5`).

**macOS** — pair, then device shows as `/dev/tty.OBDII-SPPDev` or similar.

### 3. Run

```bash
# Offline sandbox (no car needed)
python main.py --demo

# Real ELM327
python main.py --port /dev/rfcomm0
python main.py --port COM5 --baud 38400
```

---

## Mode 22 (Nissan extended) routing

Cheap ELM327 clones often ignore Mode 22 requests. A **genuine ELM327 v1.5
adapter (e.g. HT500)** handles them fine — but it still needs to route
the request to the Infiniti engine ECU explicitly.

On connect, `OBDClient._configure_nissan()` sends:

```
ATSP6         force ISO 15765-4 CAN 11-bit 500 kbps
ATSH 7E0      set request header to engine ECU
ATCRA 7E8     filter replies to engine ECU only
ATCAF1        CAN auto-formatting on
ATST32        ~200 ms response timeout
```

This is what makes VVEL / AFR / knock / oil temp / injector PW work
on the VQ37VHR without a K+DCAN cable.

## PID Probe tab

Before driving, open the **PID Probe** tab and click **Probe PIDs**.
Every PID is queried once and the table shows:

| Status | Meaning |
|---|---|
| `OK <value>` | ECU responded — gauge will work. |
| `NO DATA` | ECU doesn't expose that address (or scaling key is off by one). Auto-skipped in the main poll loop. |
| `ERR <type>` | Bus / adapter error. |

Use **Re-enable All** if you edit `config/pids.py` and want the poll
loop to retry everything without reconnecting.

## G37-specific extended (Mode 22) PIDs

The ECU exposes standard OBD-II PIDs (Mode 01) plus Nissan-proprietary
Mode 22 PIDs for VVEL, per-bank knock, injector pulse width, oil
temp, etc. Definitions live in [`config/pids.py`](config/pids.py).

Community-reported VQ37VHR addresses baked in:

| Key           | PID  | Description                      | Scaling           |
|---------------|------|----------------------------------|-------------------|
| `AFR_B1`      | 1103 | Wideband lambda, bank 1          | raw × 0.0001526   |
| `AFR_B2`      | 1104 | Wideband lambda, bank 2          | raw × 0.0001526   |
| `KNOCK_CORR`  | 1161 | Global knock correction (°)      | s8 × 0.375        |
| `VVEL_B1/B2`  | 1180/1181 | VVEL lift angle (°)         | u16 × 0.01        |
| `CAM_ADV_B1/B2` | 1190/1191 | Intake cam advance (°)    | s8 × 0.5          |
| `INJ_PW_B1/B2` | 1120/1121 | Injector pulse width (ms) | u16 × 0.004       |
| `OIL_TEMP`    | 1155 | Engine oil temperature (°C)      | s8 − 40           |
| `BATT_V`      | 110D | Battery voltage (V)              | u16 × 0.01        |
| `MAF_V`       | 1148 | MAF sensor voltage (V)           | u16 × 0.005       |

> **Verify before production logging.** Mode 22 addresses vary by ECU
> part number. Confirm scalings against your RomRaider/NissanDefinitions
> XML for your exact ROM ID and adjust `config/pids.py`. The `_mk()`
> helper + decoder factories (`_decode_u16_scaled`, `_decode_s8_scaled`)
> make this a one-line edit.

---

## Future: ROM dump via nisprog + npkern

The **Datalog / Tune** tab has a `Dump Current Tune` button wired to
[`core/tune_dumper.py`](core/tune_dumper.py). It shells out to:

```
nisprog -p <port> -r 0:<rom_size> -o tunes/rom_<timestamp>.bin
```

Prereqs before you press the button:

1. **K+DCAN USB cable** plugged in (FT232RL chipset works with nisprog).
   On Linux: `ls /dev/ttyUSB*`. On Windows: check Device Manager.
2. **Build nisprog + npkern** from
   [github.com/fenugrec/nisprog](https://github.com/fenugrec/nisprog).
   Make sure `nisprog` is on `$PATH` (or edit `TuneDumper(nisprog_bin=...)`).
3. Upload the `npkern` RAM kernel **once per ignition cycle** before a
   read — extend `tune_dumper.py` with the kernel-upload command for
   your ECU (SH7058 / SH7059 variant).
4. Key ON, engine OFF, no other OBD tools on the bus.

Open the dumped `.bin` in **RomRaider** with the matching Nissan
Definitions XML to edit maps, then flash back via nisprog.

---

## CSV datalogging

- Click **Start Datalog** on the *Datalog / Tune* tab.
- Output goes to `logs/vqtech_YYYYMMDD_HHMMSS.csv`.
- Columns: `timestamp` + every key in `STANDARD_PIDS` and
  `EXTENDED_PIDS` (missing PIDs are left blank).
- Sample rate matches `--poll-hz` (default 10 Hz).

---

## Customizing the layout

- **Which gauges appear** and their ranges / redline:
  edit `GAUGE_LAYOUT` in `config/pids.py`
  (tuple: `key, label, vmin, vmax, danger_above, unit`).
- **Which signals appear on which graph:**
  edit the `groups` list in `ui/dashboard.py::_build_graphs`.
- **Theme colors:** `config/theme.py`.
- **Polling interval:** `--poll-hz` flag.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `could not connect to ELM327` | Confirm pairing; on Linux re-bind rfcomm; check `--port`. |
| Extended PIDs all blank | Your ECU may use different Mode 22 addresses — diff against your XML defs and update `config/pids.py`. |
| UI frozen | Polling runs in a background thread; if it's stuck, check the ELM adapter baud (`--baud 38400` or `9600` depending on clone). |
| `nisprog: command not found` | Build it and put it on `$PATH`, or pass an absolute path to `TuneDumper(nisprog_bin=...)`. |

---

## Credits / prior art

- [python-obd](https://python-obd.readthedocs.io/) — ELM327 protocol.
- [Dear PyGui](https://dearpygui.readthedocs.io/) — GPU-accelerated UI.
- [fenugrec/nisprog](https://github.com/fenugrec/nisprog) +
  [npkern](https://github.com/fenugrec/npkern) — Nissan ECU I/O.
- [RomRaider](https://www.romraider.com/) +
  [NissanDefinitions](https://github.com/dave-ford/NissanECU-kernel)
  for map editing.
- Inspiration: [barracuda-fsh/pyobd](https://github.com/barracuda-fsh/pyobd),
  [szotyi41/dashboard](https://github.com/szotyi41/dashboard).
