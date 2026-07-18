#!/usr/bin/env python3
"""OLED SPI signal-integrity test.

Usage: .venv/bin/python oled_test_speed.py [bus_speed_hz]
  e.g. .venv/bin/python oled_test_speed.py 1000000

Loops a moving checkerboard + text forever so you can flex/route wires and
watch for glitches. Ctrl-C to stop. Try 4000000 (default), then 2000000,
1000000, 500000 while the assembly is inside the case.
"""
import sys
import time
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas

speed = int(sys.argv[1]) if len(sys.argv) > 1 else 4000000
print(f"SPI bus_speed_hz = {speed}")

ser = spi(device=0, port=0, bus_speed_hz=speed, gpio_DC=23, gpio_RST=24)
device = ssd1322(ser, width=256, height=64, rotate=2)

frame = 0
try:
    while True:
        with canvas(device) as draw:
            # checkerboard stresses the bus with lots of transitions
            step = 8
            for y in range(0, device.height, step):
                for x in range(0, device.width, step):
                    if ((x // step + y // step + frame) % 2) == 0:
                        draw.rectangle((x, y, x + step - 1, y + step - 1), fill="white")
            draw.text((90, 26), f"SPI {speed//1000}k", fill="black")
        frame += 1
        time.sleep(0.1)
except KeyboardInterrupt:
    device.cleanup()
    print("\nDone.")
