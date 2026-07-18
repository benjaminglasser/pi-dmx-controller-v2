#!/usr/bin/env python3
"""Simple live test for the extra button on GPIO7 (physical pin 26).

Run it, then press the extra button. Each press/release prints a line.
For comparison it also watches the reset button on GPIO25 (physical pin 22),
which is known to work — so if reset prints but extra never does, the extra
button's signal is not reaching the chip's pin 26.

Run:   .venv/bin/python test_extra_button.py     (Ctrl+C to quit)
"""
import time
import RPi.GPIO as GPIO

EXTRA = 7    # physical pin 26 (current, not working)
NEW   = 12   # physical pin 32 (candidate new pin — move the signal wire here to test)
RESET = 25   # physical pin 22 (reference — known good)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(EXTRA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(NEW,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RESET, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_e = GPIO.input(EXTRA)
last_n = GPIO.input(NEW)
last_r = GPIO.input(RESET)
extra_count = 0
new_count = 0
reset_count = 0

print("Watching EXTRA (pin 26 / GPIO7), NEW (pin 32 / GPIO12), RESET (pin 22 / GPIO25).")
print(f"Idle levels -> EXTRA={last_e}  NEW={last_n}  RESET={last_r}   (1 = not pressed)")
print("Press the buttons. Ctrl+C to quit.\n")

try:
    while True:
        e = GPIO.input(EXTRA)
        n = GPIO.input(NEW)
        r = GPIO.input(RESET)

        if e != last_e:
            if e == 0:
                extra_count += 1
                print(f"    EXTRA (pin26) pressed    [{extra_count} total]")
            else:
                print("    EXTRA (pin26) released")
            last_e = e

        if n != last_n:
            if n == 0:
                new_count += 1
                print(f">>> NEW (pin32) PRESSED      [{new_count} total]")
            else:
                print("    NEW (pin32) released")
            last_n = n

        if r != last_r:
            if r == 0:
                reset_count += 1
                print(f"    reset (pin22) pressed    [{reset_count} total]")
            else:
                print("    reset (pin22) released")
            last_r = r

        time.sleep(0.002)  # 2 ms polling

except KeyboardInterrupt:
    print(f"\nDone. EXTRA(pin26)={extra_count}  NEW(pin32)={new_count}  reset(pin22)={reset_count}")
finally:
    GPIO.cleanup()
