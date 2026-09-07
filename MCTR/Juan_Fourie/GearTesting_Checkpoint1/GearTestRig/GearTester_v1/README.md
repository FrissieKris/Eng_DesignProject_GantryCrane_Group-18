# Gear Tester — Load Cell Dashboard

A console dashboard that shows live readings from the Instrotech 4004/5004
load cell indicator and records a test to a CSV file. Designed for gear
tensile/break tests, but works for any load reading.

This guide assumes you've never used a terminal before. Follow it top to
bottom the first time; after that you'll only need the "Running it" section.

## 1. What you need

- Windows 10 or 11
- Python installed (see below if you're not sure)
- The load cell indicator connected to this PC via an RS485-to-USB adapter
  (electrical wiring is assumed already done)

## 2. Check Python is installed

Open a terminal: press the **Windows key**, type `powershell`, and press
Enter. A blue/black window will open — this is your terminal. Type:

```
python --version
```

and press Enter. If you see something like `Python 3.11.4`, you're set —
skip to step 3. If you see an error, install Python from
[python.org/downloads](https://www.python.org/downloads/). During install,
tick the box that says **"Add python.exe to PATH"** — this is important,
without it the command above won't work. After installing, close and
reopen PowerShell and try the command again.

## 3. Install the one required package

In the same terminal, navigate to this folder. If the project lives at
`C:\Development\GearTester`, type:

```
cd C:\Development\GearTester
```

Then install the dependency:

```
pip install -r requirements.txt
```

This only needs to be done once (or again if you set up a new PC).

## 4. Find which COM port the indicator is on

The RS485-USB adapter shows up as a numbered "COM port" (e.g. `COM3`).
Windows assigns this number automatically and it can change if you plug
the adapter into a different USB socket, so it's worth checking each time
if the dashboard says it can't connect.

**Easiest way — Device Manager:**
1. Press the **Windows key**, type `Device Manager`, press Enter.
2. Expand **Ports (COM & LPT)**.
3. Look for an entry like `USB Serial Port (COM3)` — the number in
   brackets is your port. If you unplug the adapter and the entry
   disappears, then plug it back in and it reappears, you've confirmed
   which one it is.

**Alternative — from the terminal**, with the adapter plugged in:

```
python -c "import serial.tools.list_ports as lp; [print(p.device, '-', p.description) for p in lp.comports()]"
```

This prints every serial port Windows currently sees, e.g.:

```
COM3 - USB Serial Port (COM3)
```

If nothing prints, the adapter isn't detected — check it's plugged in and
its driver installed (it usually installs itself automatically on first
plug-in).

## 5. Running it

In the terminal, from the `C:\Development\GearTester` folder:

```
python run_dashboard.py --port COM3
```

Replace `COM3` with whatever port you found in step 4. Leave the terminal
window open — this is the dashboard.

If your indicator's baud rate isn't the default (9600), add it, e.g.:

```
python run_dashboard.py --port COM3 --baud 19200
```

## 6. Using the dashboard

Once running, you'll see the live load reading updating several times a
second. The bottom of the screen lists the available keys:

| Key | Action |
|-----|--------|
| `s` | Start recording a test. You'll be asked for a label (e.g. the gear's name/ID) — this becomes part of the saved filename. |
| `x` | Stop the current recording and save it. Use this for a gear that **doesn't** break — just stop when you've reached your target load. |
| `a` | Turn automatic stop-on-break on/off. |
| `q` | Quit the dashboard. If a recording is running, it's saved first. |

**Automatic stop:** if the load suddenly drops a lot after reaching a
peak (a break), the dashboard detects this on its own, records a few
extra samples, and stops the recording for you — no key press needed.
This won't trigger for gears that survive the test; those are ended
manually with `x`.

Recordings are saved to the `logs` folder as CSV files, named like
`GearA17_20260907_143012.csv` (label + date + time). Each file has:

| Column | Meaning |
|--------|---------|
| `sample_no` | Sample number — use this as the X axis for a load curve |
| `elapsed_s` | Seconds since the recording started |
| `timestamp` | Real date/time of the sample |
| `load_kg` | The reading (units match `--units`, default `kg`) |

Open the CSV in Excel, or any plotting tool, to see the load curve.

## 7. Closing the dashboard

Press `q` in the terminal window, or close the window — either way, if a
recording was in progress it gets saved automatically before it exits.

## Troubleshooting

- **"could not open port 'COMx'"** — wrong port number (recheck step 4),
  or another program (or another copy of this dashboard) already has the
  port open. Close other serial programs and try again.
- **Dashboard runs but the reading never changes / says "waiting for
  data"** — check the indicator is powered on and its RS485 output/wiring
  is connected. Also check "Frame errors" isn't climbing — if it is, the
  baud rate is probably wrong (`--baud`).
- **Readings look scrambled or don't make sense** — the indicator's
  communication settings must match: protocol set to ASCIIbus (`Conn` →
  `ASCI` → `On` on the indicator), unit address between `01`-`99`, and
  the same baud rate passed to `--baud`.
