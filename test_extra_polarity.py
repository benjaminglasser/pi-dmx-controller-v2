#!/usr/bin/env python3
"""Polarity test for the extra button on GPIO7 (pin 26).

Reads GPIO7 with an internal pull-DOWN. If the button is wired active-HIGH
(GPIO7 -> 3.3V when pressed), the idle level will be 0 and it will jump to 1
when you press. That would mean the fix is purely software (use PUD_DOWN and
detect a HIGH press), not hardware.

Run:  .venv/bin/python test_extra_polarity.py   (Ctrl+C to quit)
"""
import time
import RPi.GPIO as GPIO

EXTRA = 7  # physical pin 26

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(EXTRA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

last = GPIO.input(EXTRA)
highs = 0
print("GPIO7 read with internal PULL-DOWN.")
print(f"Idle level = {last}  (if this is 0, pull-down is working)")
print("Now press the extra button. Ctrl+C to quit.\n")

try:
    while True:
        v = GPIO.input(EXTRA)
        if v != last:
            if v == 1:
                highs += 1
                print(f">>> GPIO7 went HIGH on press  [{highs} total]  --> button is ACTIVE-HIGH!")
            else:
                print("    GPIO7 back to LOW (released)")
            last = v
        time.sleep(0.002)
except KeyboardInterrupt:
    print(f"\nDone. HIGH-on-press events: {highs}")
    print("If >0: button is active-high; fix is software (PUD_DOWN + detect HIGH).")
    print("If 0 : button did not drive the pin high either; not a polarity issue.")
finally:
    GPIO.cleanup()
