#!/usr/bin/env python3
"""Clean, isolated OLED test for the SSD1322 (256x64) over 4-wire SPI.

Nothing else in the system runs here — just the display. Wiring per the
board schematic:
    OLED 4  -> SCLK (GPIO11, SPI0)
    OLED 5  -> MOSI (GPIO10, SPI0)
    OLED 14 -> DC   (GPIO23)
    OLED 15 -> RST  (GPIO24)
    OLED 16 -> CS   (CE0/GPIO8)

Usage:
    .venv/bin/python oled_clean_test.py                # default: refresh only
    .venv/bin/python oled_clean_test.py --reinit 3     # full re-init every 3s
    .venv/bin/python oled_clean_test.py --speed 1000000

Watch the counter. If it ever glitches:
  - and a periodic --reinit makes it snap back clean  -> recoverable (software
    watchdog will help).
  - and it stays glitched through re-inits            -> physical/electrical.
Ctrl-C to quit.
"""
import argparse
import time
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from luma.core.render import canvas
from PIL import ImageFont

parser = argparse.ArgumentParser()
parser.add_argument("--speed", type=int, default=4000000, help="SPI Hz")
parser.add_argument("--reinit", type=float, default=0.0,
                    help="seconds between full display re-inits (0 = never)")
args = parser.parse_args()


def make_device(speed):
    ser = spi(device=0, port=0, bus_speed_hz=speed, gpio_DC=23, gpio_RST=24)
    return ssd1322(ser, width=256, height=64, rotate=2)


def draw_frame(device, n, font):
    with canvas(device) as draw:
        # border so any edge corruption is obvious
        draw.rectangle(device.bounding_box, outline="white")
        # big readable counter
        draw.text((8, 6), "OLED CLEAN TEST", fill="white", font=font)
        draw.text((8, 30), f"frame {n:06d}", fill="white", font=font)
        # a few reference bars
        for i in range(4):
            x = 150 + i * 24
            draw.rectangle((x, 8, x + 16, 56), fill="white" if i % 2 else "black",
                           outline="white")


def main():
    print(f"SPI speed={args.speed} Hz, reinit every {args.reinit or 'never'}s")
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except Exception:
        font = ImageFont.load_default()

    device = make_device(args.speed)
    print("display initialized OK")

    n = 0
    last_reinit = time.monotonic()
    try:
        while True:
            if args.reinit and (time.monotonic() - last_reinit) >= args.reinit:
                print(f"[frame {n}] full re-init")
                try:
                    device.cleanup()
                except Exception:
                    pass
                device = make_device(args.speed)
                last_reinit = time.monotonic()

            draw_frame(device, n, font)
            n += 1
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            device.cleanup()
        except Exception:
            pass
        print("\nDone.")


if __name__ == "__main__":
    main()
