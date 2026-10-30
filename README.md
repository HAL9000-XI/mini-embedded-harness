# Mini Embedded Harness

Minimal proof of concept: GitHub Actions builds, flashes and tests an ESP32 DevKit connected by USB to an Ubuntu self-hosted runner.

## Hardware

- Classic ESP32 DevKit (`esp32dev` / ESP32-WROOM-32 class)
- USB data cable
- External LED and 220-330 ohm resistor

Wire GPIO18 -> resistor -> LED anode (long leg); LED cathode (short leg) -> GND.

## Local setup

```bash
sudo apt update
sudo apt install -y git curl python3 python3-venv python3-pip build-essential udev
sudo usermod -aG dialout "$USER"
```

Log out and back in, reconnect the board, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip platformio pyserial
pio run
```

Find the serial device:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Local flash and test:

```bash
export ESP32_PORT=/dev/ttyUSB0   # change to the actual device
pio run -t upload --upload-port "$ESP32_PORT"
python testbench/test_blink.py
```

## GitHub Actions self-hosted runner

1. Create a **private** GitHub repository and push this project.
2. In repository Settings -> Actions -> Runners -> New self-hosted runner, select Linux and the correct architecture.
3. Follow GitHub's current download/configuration commands on the Ubuntu PC. Do not reuse or publish the one-time registration token.
4. During configuration, add the custom label `esp32-testbench`.
5. Install the runner as a service if desired, using GitHub's generated `svc.sh` instructions.
6. In repository Settings -> Secrets and variables -> Actions -> Variables, optionally add `ESP32_PORT` with the actual port, e.g. `/dev/ttyUSB0`.
7. Run Actions -> ESP32 blink hardware test -> Run workflow.

The workflow is manual (`workflow_dispatch`) and expects labels `self-hosted`, `linux`, `x64`, and `esp32-testbench`.

## Safety

- Keep this repository private for the initial experiment.
- Do not run untrusted pull-request code on a self-hosted runner attached to hardware.
- Do not expose the runner or serial device to the public internet.
- Keep the ESP32 connected to the same USB port while the test runs.
- The test validates serial-reported GPIO transitions and timing, not emitted light. Add a photodiode/light sensor for independent optical verification.

## Expected serial protocol

```text
HARNESS:BOOT
HARNESS:LED=1;T=1500
HARNESS:LED=0;T=2000
```
