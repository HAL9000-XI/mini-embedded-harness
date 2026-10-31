# Mini Embedded Harness

Minimal local ESP32 test bench for Ubuntu.

## Hardware
- Classic ESP32 DevKit with CP2102 USB serial adapter
- GPIO18 output; optional LED and 220–330 ohm series resistor to GND
- ESP32 GPIO is 3.3 V; do not apply 5 V.

## Install
From this directory:

```bash
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install platformio pyserial
```

## Run

Close screen/picocom or any program using the serial port:

```bash
source .venv/bin/activate
python run_tests.py
```

The runner checks files and CR+LF firmware configuration, runs offline parser
regressions (CR+LF, CR-only, LF-only, unterminated input), builds firmware,
flashes the ESP32, and verifies actual serial output, alternating states and
blink timing.

If port discovery is ambiguous:

```bash
ESP32_PORT=/dev/ttyUSB0 python run_tests.py
```

## Scope

The hardware test currently validates firmware-reported GPIO state and timing
over serial. It does not yet independently measure the physical GPIO waveform.
Saleae/sigrok capture and waveform analysis are planned next.
