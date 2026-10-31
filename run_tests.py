#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST_DIR = ROOT / "testbench"
FIRMWARE = ROOT / "src" / "main.cpp"
PROTOCOL_TEST = TEST_DIR / "test_serial_protocol.py"
HARDWARE_TEST = TEST_DIR / "test_blink.py"
KNOWN_USB_IDS = {
    (0x10C4, 0xEA60), (0x1A86, 0x7523), (0x1A86, 0x55D4),
    (0x0403, 0x6001), (0x303A, 0x1001),
}

def run_step(title, command):
    print("\n" + "=" * 68, flush=True)
    print(title, flush=True)
    print("=" * 68, flush=True)
    subprocess.run(command, cwd=ROOT, check=True)

def check_files():
    required = [ROOT / "platformio.ini", FIRMWARE,
                TEST_DIR / "serial_protocol.py", PROTOCOL_TEST, HARDWARE_TEST]
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Required file missing: {path}")
    source = FIRMWARE.read_text(encoding="utf-8")
    if not source.lstrip().startswith("#include"):
        raise RuntimeError("src/main.cpp does not look like C++ firmware.")
    if r'"HARNESS:LED=%d;T=%lu\r\n"' not in source:
        raise RuntimeError(r'Firmware LED message must use "\r\n".')

def find_port():
    configured = os.getenv("ESP32_PORT")
    if configured:
        return configured
    from serial.tools import list_ports
    ports = [p for p in list_ports.comports()
             if (p.vid, p.pid) in KNOWN_USB_IDS]
    if len(ports) != 1:
        raise RuntimeError(
            f"Expected one ESP32 adapter, found {len(ports)}. Set ESP32_PORT=/dev/ttyUSB0 if needed."
        )
    device = Path(ports[0].device).resolve()
    by_id = Path("/dev/serial/by-id")
    if by_id.exists():
        for link in by_id.iterdir():
            if link.resolve() == device:
                return str(link)
    return str(device)

def main():
    print("ESP32 AUTOMATED TEST BENCH", flush=True)
    check_files()
    pio = shutil.which("pio")
    if not pio:
        raise RuntimeError("PlatformIO CLI 'pio' not found. Activate .venv and install platformio.")
    port = find_port()
    print(f"ESP32 detected: {port}", flush=True)
    run_step("STEP 1: OFFLINE SERIAL PROTOCOL REGRESSION TESTS",
             [sys.executable, str(PROTOCOL_TEST)])
    run_step("STEP 2: BUILD FIRMWARE", [pio, "run"])
    run_step("STEP 3: FLASH ESP32",
             [pio, "run", "--target", "upload", "--upload-port", port])
    run_step("STEP 4: RUN ESP32 HARDWARE SERIAL TEST",
             [sys.executable, str(HARDWARE_TEST), "--port", port])
    print("\n" + "=" * 68)
    print("ALL TESTS PASSED")
    print("=" * 68)

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, AssertionError) as exc:
        print(f"\nTEST BENCH FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
