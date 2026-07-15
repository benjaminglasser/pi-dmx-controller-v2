#!/usr/bin/env python3
"""Encoder/button test using same bulk-read method as dmx_audio_react.py."""
import os, time, threading, sys
os.environ.setdefault('GPIOZERO_PIN_FACTORY', 'rpigpio')

import board, busio
import RPi.GPIO as GPIO
from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas

# --- MCP23017 (exact same init as dmx_audio_react.py) ---
i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c, address=0x20)

ENC1_CLK,ENC1_DT,ENC1_SW = 8,9,10
ENC2_CLK,ENC2_DT,ENC2_SW = 11,12,13
ENC3_CLK,ENC3_DT,ENC3_SW = 14,0,1
ENC4_CLK,ENC4_DT,ENC4_SW = 2,3,4
ENC5_CLK,ENC5_DT          = 5,6
ENC5_SW_GPIO    = 17
RESET_BTN_GPIO  = 25
EXTRA_BTN_GPIO  = 7

mcp_input_pins = [
    ENC1_CLK,ENC1_DT,ENC1_SW,
    ENC2_CLK,ENC2_DT,ENC2_SW,
    ENC3_CLK,ENC3_DT,ENC3_SW,
    ENC4_CLK,ENC4_DT,ENC4_SW,
    ENC5_CLK,ENC5_DT,
]
for idx in mcp_input_pins:
    pin = mcp.get_pin(idx)
    pin.direction = Direction.INPUT
    pin.pull = Pull.UP

GPIO.setmode(GPIO.BCM)
for bcm in [ENC5_SW_GPIO, RESET_BTN_GPIO, EXTRA_BTN_GPIO]:
    GPIO.setup(bcm, GPIO.IN, pull_up_down=GPIO.PUD_UP)

ser = spi(device=0, port=0, bus_speed_hz=4000000, gpio_DC=23, gpio_RST=24)
device = ssd1322(ser, width=256, height=64, rotate=2)

def mcp_read_all():
    return mcp.gpio  # bulk 16-bit read, same as main app

def bit(snapshot, idx):
    return (snapshot >> idx) & 1

counts   = [0] * 5
sw_flash = [False] * 5
rst_flash = False
ext_flash = False
lock = threading.Lock()

def poll():
    global rst_flash, ext_flash
    snap = mcp_read_all()
    last_clk = [bit(snap, ENC1_CLK), bit(snap, ENC2_CLK), bit(snap, ENC3_CLK),
                bit(snap, ENC4_CLK), bit(snap, ENC5_CLK)]
    sw_pins  = [ENC1_SW, ENC2_SW, ENC3_SW, ENC4_SW, None]
    dt_pins  = [ENC1_DT, ENC2_DT, ENC3_DT, ENC4_DT, ENC5_DT]
    clk_pins = [ENC1_CLK, ENC2_CLK, ENC3_CLK, ENC4_CLK, ENC5_CLK]
    last_sw  = [bit(snap, sw) if sw else GPIO.input(ENC5_SW_GPIO) for sw in sw_pins]
    last_rst = GPIO.input(RESET_BTN_GPIO)
    last_ext = GPIO.input(EXTRA_BTN_GPIO)

    while True:
        snap = mcp_read_all()
        for i in range(5):
            clk = bit(snap, clk_pins[i])
            dt  = bit(snap, dt_pins[i])
            if not clk and last_clk[i]:
                with lock:
                    counts[i] += 1 if dt else -1
            last_clk[i] = clk

            sw = bit(snap, sw_pins[i]) if sw_pins[i] is not None else GPIO.input(ENC5_SW_GPIO)
            if not sw and last_sw[i]:
                with lock:
                    sw_flash[i] = True
            last_sw[i] = sw

        rst = GPIO.input(RESET_BTN_GPIO)
        ext = GPIO.input(EXTRA_BTN_GPIO)
        with lock:
            if not rst and last_rst: rst_flash = True
            if not ext and last_ext: ext_flash = True
        last_rst, last_ext = rst, ext
        time.sleep(0.001)

threading.Thread(target=poll, daemon=True).start()
print("Encoder test — turn encoders, press switches/buttons. Ctrl+C to exit.\n")

first = True
try:
    while True:
        with lock:
            c  = list(counts)
            sw = list(sw_flash)
            rf = rst_flash
            ef = ext_flash
            for i in range(5): sw_flash[i] = False
            rst_flash = False
            ext_flash = False

        with canvas(device) as draw:
            draw.text((0,  0), f"E1:{c[0]:+4d}  E2:{c[1]:+4d}  E3:{c[2]:+4d}", fill="white")
            draw.text((0, 14), f"E4:{c[3]:+4d}  E5:{c[4]:+4d}", fill="white")
            sw_str = " ".join(f"E{i+1}SW" for i in range(5) if sw[i]) or "-"
            draw.text((0, 28), f"SW:  {sw_str}", fill="white")
            btn_str = " ".join(filter(None,["RESET" if rf else "","EXTRA" if ef else ""])) or "-"
            draw.text((0, 42), f"BTN: {btn_str}", fill="white")
            draw.text((0, 54), "Turn/press to test", fill="white")

        sw_str  = " ".join(f"E{i+1}SW" for i in range(5) if sw[i]) or "-"
        btn_str = " ".join(filter(None,["RESET" if rf else "","EXTRA" if ef else ""])) or "-"
        lines = [
            "┌──────────────────────────────────────┐",
            f"│  E1:{c[0]:+5d}  E2:{c[1]:+5d}  E3:{c[2]:+5d}     │",
            f"│  E4:{c[3]:+5d}  E5:{c[4]:+5d}               │",
            "├──────────────────────────────────────┤",
            f"│  SW:  {'  '.join(f'[E{i+1}]' if sw[i] else f' E{i+1} ' for i in range(5))}  │",
            f"│  BTN: {'[RESET]' if rf else ' RESET '}  {'[EXTRA]' if ef else ' EXTRA '}       │",
            "└──────────────────────────────────────┘",
        ]
        if not first:
            sys.stdout.write(f"\033[{len(lines)}A")
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        first = False
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nDone.")
finally:
    device.cleanup()
    GPIO.cleanup()
