#!/usr/bin/env python3
import os
import re
import sys
import time
from serial import Serial, SerialException
from serial.tools import list_ports

BAUD = 115200
TEST_SECONDS = 18
MIN_TRANSITIONS = 8
MIN_INTERVAL_MS = 350
MAX_INTERVAL_MS = 700

def choose_port():
    configured = os.environ.get("ESP32_PORT")
    if configured:
        return configured

    ports = list(list_ports.comports())
    # Common USB-UART bridges: CP210x, CH340, FTDI; native Espressif USB.
    known = []
    for p in ports:
        if p.vid in (0x10C4, 0x1A86, 0x0403, 0x303A):
            known.append(p.device)

    if len(known) == 1:
        return known[0]
    if len(ports) == 1:
        return ports[0].device

    found = ", ".join(p.device for p in ports) or "none"
    raise RuntimeError(
        f"Could not uniquely identify ESP32 serial port (found: {found}). "
        "Set ESP32_PORT, e.g. /dev/ttyUSB0."
    )

def main():
    port = choose_port()
    print(f"Using ESP32 serial port: {port}")
    transitions = []
    boot_seen = False
    deadline = time.monotonic() + TEST_SECONDS

    try:
        # Opening the port may reset some DevKit boards; wait for boot marker.
        with Serial(port, BAUD, timeout=0.25) as ser:
            while time.monotonic() < deadline:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                print(line)

                if "HARNESS:BOOT" in line:
                    boot_seen = True

                match = re.search(r"HARNESS:LED=([01]);T=(\d+)", line)
                if match:
                    transitions.append((int(match.group(1)), int(match.group(2))))
                    if len(transitions) >= MIN_TRANSITIONS:
                        break

    except SerialException as exc:
        raise RuntimeError(f"Serial communication failed: {exc}") from exc

    if not boot_seen:
        raise AssertionError("Boot marker not observed")
    if len(transitions) < MIN_TRANSITIONS:
        raise AssertionError(
            f"Expected at least {MIN_TRANSITIONS} transitions; got {len(transitions)}"
        )

    states = [state for state, _ in transitions]
    if any(states[i] == states[i - 1] for i in range(1, len(states))):
        raise AssertionError(f"LED states did not alternate: {states}")

    intervals = [
        transitions[i][1] - transitions[i - 1][1]
        for i in range(1, len(transitions))
    ]
    bad = [dt for dt in intervals if not MIN_INTERVAL_MS <= dt <= MAX_INTERVAL_MS]
    if bad:
        raise AssertionError(f"Blink interval outside tolerance: {bad}; all={intervals}")

    print(
        "PASS: boot marker, alternating GPIO reports and blink timing verified. "
        f"Intervals (ms): {intervals}"
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
