#!/usr/bin/env python3
"""OLED hardware test — fills screen white, then black, then shows text."""
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas
import time

ser = spi(device=0, port=0, bus_speed_hz=4000000, gpio_DC=23, gpio_RST=24)
device = ssd1322(ser, width=256, height=64, rotate=2)

print("White fill...")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, fill="white")
time.sleep(2)

print("Black fill...")
with canvas(device) as draw:
    draw.rectangle(device.bounding_box, fill="black")
time.sleep(1)

print("Text...")
with canvas(device) as draw:
    draw.text((10, 20), "DMX OK", fill="white")
time.sleep(3)

device.cleanup()
print("Done.")
