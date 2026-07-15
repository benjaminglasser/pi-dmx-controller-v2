#!/usr/bin/env python3
"""Friendly live input monitor for the HiFiBerry DAC+ADC.

Shows two big color bars (LEFT / RIGHT) that stay in one place and tell you
plainly whether audio is reaching the ADC:

    GREEN  "SIGNAL"  -> good audio is coming in
    YELLOW "faint"   -> something's there but very weak
    GRAY   "silent"  -> nothing but noise floor

Usage:
    .venv/bin/python adc_meter.py            # auto-pick HiFiBerry
    .venv/bin/python adc_meter.py --device 1 # force a device index
Press Ctrl-C to quit.
"""
import argparse
import sys
import time
import numpy as np
import sounddevice as sd

ap = argparse.ArgumentParser()
ap.add_argument("--device", type=int, default=None, help="PortAudio device index")
ap.add_argument("--sr", type=int, default=48000)
args = ap.parse_args()

# ---- pick device ----------------------------------------------------------
dev = args.device
if dev is None:
    for i, d in enumerate(sd.query_devices()):
        if int(d.get("max_input_channels", 0) or 0) >= 1 and "hifiberry" in d["name"].lower():
            dev = i
            break
if dev is None:
    print("No HiFiBerry input found. Devices:")
    print(sd.query_devices())
    sys.exit(1)

info = sd.query_devices(dev)

# ---- thresholds (dBFS) ----------------------------------------------------
SIGNAL_DB = -45.0   # above this = clearly good
FAINT_DB = -60.0    # between faint and signal = weak
BAR_MIN, BAR_MAX = -70.0, 0.0
WIDTH = 44

# ---- ANSI helpers ---------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
CYAN = "\033[96m"
WHITE = "\033[97m"
HOME = "\033[H"
CLR_EOS = "\033[J"
HIDE_CUR = "\033[?25l"
SHOW_CUR = "\033[?25h"

# ---- shared state ---------------------------------------------------------
state = {
    "rms": [-99.0, -99.0],   # smoothed level per channel
    "peakhold": [-99.0, -99.0],
    "peak_t": [0.0, 0.0],
    "sessionmax": [-99.0, -99.0],
}


def db(x):
    return 20 * np.log10(x) if x > 1e-9 else -99.0


def cb(indata, frames, time_info, status):
    now = time.monotonic()
    ch = min(indata.shape[1], 2)
    for c in range(ch):
        x = indata[:, c]
        rms = db(float(np.sqrt(np.mean(x ** 2))))
        pk = db(float(np.max(np.abs(x))))
        # smooth the moving bar a little so it's readable
        prev = state["rms"][c]
        state["rms"][c] = rms if prev < -98 else prev * 0.6 + rms * 0.4
        # peak hold with 1.2s decay
        if pk > state["peakhold"][c] or (now - state["peak_t"][c]) > 1.2:
            state["peakhold"][c] = pk
            state["peak_t"][c] = now
        if pk > state["sessionmax"][c]:
            state["sessionmax"][c] = pk


def classify(level_db):
    if level_db >= SIGNAL_DB:
        return GREEN, "SIGNAL", True
    if level_db >= FAINT_DB:
        return YELLOW, "faint", False
    return GRAY, "silent", False


def bar(level_db, peak_db, color):
    span = BAR_MAX - BAR_MIN
    frac = max(0.0, min(1.0, (level_db - BAR_MIN) / span))
    n = int(round(frac * WIDTH))
    # peak marker position
    pfrac = max(0.0, min(1.0, (peak_db - BAR_MIN) / span))
    pmark = min(WIDTH - 1, int(round(pfrac * WIDTH)))
    cells = []
    for i in range(WIDTH):
        if i == pmark and peak_db > BAR_MIN:
            cells.append(f"{WHITE}|{color}")
        elif i < n:
            cells.append("█")
        else:
            cells.append(f"{DIM}·{RESET}{color}")
    return color + "".join(cells) + RESET


def render():
    lines = []
    lines.append(f"{BOLD}{CYAN}  HiFiBerry ADC — Live Input Monitor{RESET}")
    lines.append(f"{DIM}  device [{dev}] {info['name'][:52]}{RESET}")
    lines.append("")
    lines.append(f"{DIM}  Play audio into the input jacks, OR touch the input")
    lines.append(f"  jack's center pin with a finger — a live input jumps.{RESET}")
    lines.append("")
    any_signal = False
    for c, name in ((0, "LEFT "), (1, "RIGHT")):
        lvl = state["rms"][c]
        pk = state["peakhold"][c]
        color, label, is_sig = classify(pk)
        any_signal = any_signal or is_sig
        lines.append(
            f"  {BOLD}{name}{RESET} [{bar(lvl, pk, color)}] "
            f"{color}{pk:6.0f} dB  {label:<7}{RESET}"
        )
    lines.append("")
    if any_signal:
        verdict = f"{BOLD}{GREEN}  ✅  AUDIO IS COMING IN{RESET}"
    elif max(state["peakhold"]) >= FAINT_DB:
        verdict = f"{BOLD}{YELLOW}  ⚠   only a FAINT signal — input too weak{RESET}"
    else:
        verdict = f"{BOLD}{GRAY}  🔇  SILENT — no signal reaching the ADC{RESET}"
    lines.append(verdict)
    lines.append("")
    lines.append(
        f"{DIM}  loudest so far:  LEFT {state['sessionmax'][0]:.0f} dB   "
        f"RIGHT {state['sessionmax'][1]:.0f} dB       Ctrl-C to quit{RESET}"
    )
    return "\n".join(lines)


print(HIDE_CUR + "\033[2J", end="")
try:
    with sd.InputStream(device=dev, channels=2, samplerate=args.sr,
                        blocksize=1024, callback=cb):
        while True:
            sys.stdout.write(HOME + render() + CLR_EOS)
            sys.stdout.flush()
            time.sleep(0.06)
except KeyboardInterrupt:
    pass
finally:
    print(SHOW_CUR + RESET)
    print("\nstopped.")
