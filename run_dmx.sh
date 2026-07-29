#!/usr/bin/env bash
# Manual start: same env as systemd/pi-dmx.service (HiFiBerry input, full encoders, TUI + OLED).
# Python equivalent (clears AUDIO_DEVICE, same defaults):  ./.venv/bin/python scripts/dev_ui.py
# Stop the service first if it is running:  sudo systemctl stop pi-dmx.service
set -euo pipefail

cd /home/pi/pi-dmx-controller-v2

# Avoid stale index from an old shell (e.g. AUDIO_DEVICE=2) breaking startup.
unset AUDIO_DEVICE

export AUDIO_INPUT_CHANNEL=left
export DISABLE_I2S_ENCODERS=1
export AUDIO_DEVICE_NAME=hifiberry

# Detection mode: classic|compander|kick|old|manual. Override to A/B, e.g.:
#   DETECT_MODE=manual ./run_dmx.sh
export DETECT_MODE=${DETECT_MODE:-classic}

# AGC: "scaled" = a fixed per-frequency gain curve that rises with the selected band center
# (highs get more boost than lows), so a snare (mids) or hats (highs) drive output without
# hand-tuning — and, unlike "calibrate", it never locks onto a wrong reference (e.g. a
# kick-less section). Tune the tilt with FREQ_GAIN_SLOPE (0.5 ≈ pink). Alternatives:
#   AGC_GAIN_MODE=calibrate ./run_dmx.sh   (auto-lock off in-band hits)
#   AGC_GAIN_MODE=fixed ./run_dmx.sh       (one constant gain at all frequencies)
export AGC_GAIN_MODE=${AGC_GAIN_MODE:-scaled}

export NOISE_GATE_ON=0
export ENABLE_TUI=1
export DMX_BACKEND=uart

exec /home/pi/pi-dmx-controller-v2/.venv/bin/python dmx_audio_react.py
