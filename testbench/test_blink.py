
import os
import re
import sys
import time

from serial import Serial
from serial.tools import list_ports
from serial import SerialException

BAUD = 115200
MIN_TRANSITIONS = 8
TEST_TIMEOUT_SECONDS = 18


def find_port():
    configured = os.getenv("ESP32_PORT")

    if configured:
        return configured

    ports = list(list_ports.comports())

    # Common USB-to-serial chip identifiers.
    known_ids = {
        (0x10C4, 0xEA60),  # Silicon Labs CP210x
        (0x1A86, 0x7523),  # CH340
        (0x1A86, 0x55D4),  # CH9102
        (0x0403, 0x6001),  # FTDI
        (0x303A, 0x1001),  # Espressif USB JTAG/serial
    }

    matches = [
        port.device
        for port in ports
        if (port.vid, port.pid) in known_ids
    ]

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise RuntimeError(
            "No supported ESP32 USB serial port found. "
            "Set ESP32_PORT to the correct serial device."
        )

    raise RuntimeError(
        f"Multiple possible ESP32 ports found: {matches}. "
        "Set ESP32_PORT to the correct serial device."
    )


def main():
    port = find_port()
    print(f"Using ESP32 serial port: {port}")

    boot_seen = False
    transitions = []
    deadline = time.monotonic() + TEST_TIMEOUT_SECONDS

    try:
        with Serial(port, BAUD, timeout=0.25) as ser:
            # Reset the ESP32 to capture its boot message.
            ser.dtr = False
            ser.rts = True
            time.sleep(0.1)
            ser.rts = False
            time.sleep(0.1)
            ser.reset_input_buffer()

            while time.monotonic() < deadline:
                raw = ser.readline()

                if not raw:
                    continue

                line = raw.decode(
                    "utf-8", errors="replace"
                ).strip()

                print(line)

                if "HARNESS:BOOT" in line:
                    boot_seen = True

                match = re.search(
                    r"HARNESS:LED=([01]);T=(\d+)", line
                )

                if match:
                    state = int(match.group(1))
                    timestamp = int(match.group(2))
                    transitions.append((state, timestamp))

                    if len(transitions) >= MIN_TRANSITIONS:
                        break

    except SerialException as exc:
        raise RuntimeError(
            f"Serial communication failed: {exc}"
        ) from exc

    if not boot_seen:
        raise AssertionError("Boot marker not observed")

    if len(transitions) < MIN_TRANSITIONS:
        raise AssertionError(
            f"Expected at least {MIN_TRANSITIONS} LED transitions, "
            f"got {len(transitions)}"
        )

    # Check that LED states alternate.
    for previous, current in zip(
        transitions, transitions[1:]
    ):
        if previous[0] == current[0]:
            raise AssertionError(
                "LED states did not alternate"
            )

    # Check that blink intervals are approximately 500 ms.
    intervals = [
        current[1] - previous[1]
        for previous, current in zip(
            transitions, transitions[1:]
        )
    ]

    for interval in intervals:
        if not 350 <= interval <= 700:
            raise AssertionError(
                f"Blink interval out of range: {interval} ms"
            )

    print(
        f"PASS: boot marker observed, "
        f"{len(transitions)} transitions verified."
    )


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
