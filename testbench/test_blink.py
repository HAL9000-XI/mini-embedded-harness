#!/usr/bin/env python3
import argparse
import os
import re
import time
from pathlib import Path
from serial import Serial, SerialException
from serial.tools import list_ports
from serial_protocol import read_crlf_line

BAUD = 115200
MIN_TRANSITIONS = 8
TEST_TIMEOUT_SECONDS = 18
KNOWN_USB_IDS = {
    (0x10C4, 0xEA60), (0x1A86, 0x7523), (0x1A86, 0x55D4),
    (0x0403, 0x6001), (0x303A, 0x1001),
}

def find_port():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    args = parser.parse_args()
    if args.port:
        return args.port
    if os.getenv("ESP32_PORT"):
        return os.environ["ESP32_PORT"]
    ports = [p for p in list_ports.comports()
             if (p.vid, p.pid) in KNOWN_USB_IDS]
    if len(ports) != 1:
        raise RuntimeError(
            f"Expected one ESP32 adapter, found {len(ports)}. Use --port or ESP32_PORT."
        )
    device = Path(ports[0].device).resolve()
    by_id = Path("/dev/serial/by-id")
    if by_id.exists():
        for link in by_id.iterdir():
            if link.resolve() == device:
                return str(link)
    return str(device)

def main():
    port = find_port()
    print(f"Using ESP32 serial port: {port}", flush=True)
    boot_seen = False
    transitions = []
    deadline = time.monotonic() + TEST_TIMEOUT_SECONDS
    try:
        with Serial(port, BAUD, timeout=0.1) as ser:
            ser.dtr = False
            ser.rts = True
            time.sleep(0.1)
            ser.rts = False
            time.sleep(0.2)
            ser.reset_input_buffer()
            while time.monotonic() < deadline:
                line = read_crlf_line(ser, timeout=1.0)
                if line is None:
                    continue
                print(line, flush=True)
                if line == "HARNESS:BOOT":
                    boot_seen = True
                match = re.fullmatch(r"HARNESS:LED=([01]);T=(\d+)", line)
                if match:
                    transitions.append((int(match.group(1)), int(match.group(2))))
                    if len(transitions) >= MIN_TRANSITIONS:
                        break
    except SerialException as exc:
        raise RuntimeError(f"Serial communication failed: {exc}") from exc
    if not boot_seen:
        raise AssertionError("Boot marker not observed")
    if len(transitions) < MIN_TRANSITIONS:
        raise AssertionError(f"Expected {MIN_TRANSITIONS} transitions, got {len(transitions)}")
    for previous, current in zip(transitions, transitions[1:]):
        if previous[0] == current[0]:
            raise AssertionError("GPIO states did not alternate")
    intervals = [b[1] - a[1] for a, b in zip(transitions, transitions[1:])]
    for interval in intervals:
        if not 350 <= interval <= 700:
            raise AssertionError(f"Blink interval out of range: {interval} ms")
    print("\nPASS: boot marker received")
    print("PASS: CR+LF verified on every received line")
    print(f"PASS: {len(transitions)} GPIO transitions verified")
    print(f"PASS: blink intervals verified: {intervals}")
    print("\nHARDWARE TEST PASSED")

if __name__ == "__main__":
    main()
