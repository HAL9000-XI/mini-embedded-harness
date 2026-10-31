"""Offline CR+LF parser regression tests; no ESP32 required."""
from serial_protocol import read_crlf_line, SerialProtocolError

class FakeSerial:
    def __init__(self, payload):
        self.payload = bytearray(payload)
    def read(self, size=1):
        if not self.payload:
            return b""
        result = self.payload[:size]
        del self.payload[:size]
        return bytes(result)

def expect_rejected(payload, description):
    try:
        read_crlf_line(FakeSerial(payload), timeout=0.02)
    except SerialProtocolError:
        print(f"PASS: {description} rejected")
    else:
        raise AssertionError(f"{description} was incorrectly accepted")

def main():
    assert read_crlf_line(FakeSerial(b"HARNESS:TEST\r\n")) == "HARNESS:TEST"
    print("PASS: CR+LF accepted")
    expect_rejected(b"HARNESS:TEST\r", "CR-only")
    expect_rejected(b"HARNESS:TEST\n", "LF-only")
    expect_rejected(b"HARNESS:TEST", "unterminated line")
    print("PASS: all serial protocol regression tests")

if __name__ == "__main__":
    main()
