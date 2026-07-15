#!/usr/bin/env python3
"""Sends all DMX channels at full (255) continuously. Stop with Ctrl+C."""
import os, time, fcntl, serial

DEVICE = os.environ.get("DMX_UART_DEVICE", "/dev/serial0")
TIOCSBRK = 0x5427
TIOCCBRK = 0x5428

ser = serial.Serial(
    port=DEVICE, baudrate=250000,
    bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO, timeout=0, write_timeout=0, exclusive=True,
)

def send_frame(vals):
    fd = ser.fileno()
    fcntl.ioctl(fd, TIOCSBRK, 0); time.sleep(0.000092)
    fcntl.ioctl(fd, TIOCCBRK, 0); time.sleep(0.000012)
    buf = bytearray([0x00] + list(vals))
    ser.write(buf); ser.flush()

# 512 channels all at 255
frame = [255] * 512
print(f"Sending all 512 channels at 255 on {DEVICE}. Ctrl+C to stop.")
try:
    while True:
        send_frame(frame)
        time.sleep(0.04)  # ~25 Hz
except KeyboardInterrupt:
    print("\nSending zeros...")
    send_frame([0] * 512)
finally:
    ser.close()
