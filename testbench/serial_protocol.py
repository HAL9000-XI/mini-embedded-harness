"""Strict CR+LF serial line reader."""
import time

class SerialProtocolError(AssertionError):
    pass

def read_crlf_line(ser, timeout=1.0):
    """Return one decoded line; accept CR+LF only."""
    data = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        byte = ser.read(1)
        if not byte:
            continue
        if byte == b"\n":
            if not data or data[-1] != 0x0D:
                raise SerialProtocolError(
                    f"Missing CR before LF. Received: {bytes(data) + byte!r}"
                )
            return data[:-1].decode("utf-8", errors="strict")
        if byte == b"\r":
            while time.monotonic() < deadline:
                following = ser.read(1)
                if not following:
                    continue
                if following != b"\n":
                    raise SerialProtocolError(
                        "Missing LF after CR. "
                        f"Received: {bytes(data) + byte + following!r}"
                    )
                return data.decode("utf-8", errors="strict")
            raise SerialProtocolError(
                f"Missing LF after CR. Received: {bytes(data) + byte!r}"
            )
        data.extend(byte)
    if data:
        raise SerialProtocolError(
            f"Incomplete serial line (missing CR+LF): {bytes(data)!r}"
        )
    return None
