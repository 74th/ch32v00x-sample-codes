"""PC-side Pico fixture client for protocol v2 and explicit legacy v1 reads."""
from __future__ import annotations

import time
from dataclasses import dataclass

PICO_VID, PICO_PID = 0x2E8A, 0x000A


class PicoError(Exception):
    pass


class PicoTimeout(PicoError):
    pass


class PicoProtocolError(PicoError):
    pass


class PicoCanceled(PicoError):
    pass


def discover(comports, port=None, timeout=10.0, sleep=time.sleep, clock=time.monotonic):
    """Return the one Pico device; explicit `port` wins. 0 -> wait then timeout, >1 -> stop."""
    if port:
        return port
    deadline = clock() + timeout
    while True:
        found = [p.device for p in comports() if p.vid == PICO_VID and p.pid == PICO_PID]
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            raise PicoError(f"{len(found)} Picos found; select one explicitly")
        if clock() >= deadline:
            raise PicoTimeout("Pico USB serial device not found")
        sleep(0.2)


@dataclass
class Response:
    id: int
    ok: bool
    fields: list


class PicoClient:
    def __init__(self, link, timeout=2.0, clock=time.monotonic):
        self.link = link  # object with write(bytes), readline()->bytes (b'' on timeout)
        self.timeout = timeout
        self.clock = clock
        self._id = 0
        self.caps: dict = {}

    def request(self, cmd, *args) -> Response:
        self._id += 1
        rid = self._id
        self.link.write((" ".join([str(rid), cmd, *map(str, args)]) + "\n").encode())
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            raw = self.link.readline()
            if not raw:
                continue
            try:
                parts = raw.decode("ascii").split()
                got = int(parts[0])
                status = parts[1]
            except (UnicodeDecodeError, ValueError, IndexError) as exc:
                raise PicoProtocolError(f"invalid response {raw!r}") from exc
            if got != rid:
                continue  # stale response from an earlier request
            if status not in ("OK", "ERR"):
                raise PicoProtocolError(f"invalid status {status!r}")
            return Response(got, status == "OK", parts[2:])
        raise PicoTimeout(f"no response to {cmd} within {self.timeout}s")

    def negotiate(self, required=()):
        r = self.request("CAPS")
        if not r.ok:
            raise PicoProtocolError(f"CAPS rejected: {r.fields}")
        self.caps = dict(f.split("=", 1) for f in r.fields if "=" in f)
        missing = [c for c in required if c not in self.caps.get("cmds", "").split(",")]
        if missing:
            raise PicoError(f"capability not available: {', '.join(missing)}")
        return self.caps

    def reset_safe(self):
        r = self.request("RESET_SAFE")
        if not r.ok:
            raise PicoError(f"RESET_SAFE failed: {r.fields}")


    def sample_gpio(self, pin, count=300, interval_us=10000, legacy=False, sequence=False):
        """Acquire samples; legacy is explicitly selected and only supports GP0's fixed window."""
        if legacy:
            if sequence:
                raise PicoError("legacy v1 has no cancellable sequence")
            if (pin, count, interval_us) != (0, 300, 10000):
                raise PicoError("legacy v1 only supports GP0, 300 points, 10000 us")
            self.link.write(b"s")
            deadline = self.clock() + self.timeout
            while self.clock() < deadline:
                raw = self.link.readline()
                if not raw:
                    continue
                try:
                    parts = raw.decode("ascii").split()
                except UnicodeDecodeError as exc:
                    raise PicoProtocolError("non-ASCII v1 response") from exc
                if len(parts) != 3 or parts[:2] != ["PICO_GPIO_V1", "10000"]:
                    raise PicoProtocolError("invalid v1 response")
                samples = parts[2]
                if len(samples) != 300 or set(samples) - {"0", "1"}:
                    raise PicoProtocolError("invalid v1 samples")
                return samples
            raise PicoTimeout("no legacy GPIO response")
        result = self.request("GPIO_SEQUENCE" if sequence else "GPIO_SAMPLE", pin, count, interval_us)
        if not result.ok:
            if result.fields and result.fields[0] == "CANCELED":
                raise PicoCanceled("GPIO sequence canceled")
            raise PicoError(f"GPIO sample failed: {result.fields}")
        fields = dict(item.split("=", 1) for item in result.fields if "=" in item)
        if fields.get("pin") != str(pin) or fields.get("count") != str(count) or fields.get("interval_us") != str(interval_us):
            raise PicoProtocolError("sample settings mismatch")
        samples = fields.get("samples", "")
        if len(samples) != count or set(samples) - {"0", "1"}:
            raise PicoProtocolError("invalid samples")
        return samples

    def cancel_sequence(self):
        """Cancel an in-flight GPIO sequence; invoke from a separate controlling thread."""
        self.link.write(b"!")


def wait_ready(comports, open_link, port=None, timeout=30.0, sleep=time.sleep, clock=time.monotonic):
    """Wait for a uniquely selected serial device and its v2 CAPS after reboot.

    The caller supplies a context-manager factory accepting (port, timeout).
    Ambiguous devices fail immediately; transient open/response failures are retried.
    """
    deadline = clock() + timeout
    last_error = None
    while clock() < deadline:
        ports = [p.device for p in comports() if p.vid == PICO_VID and p.pid == PICO_PID] if not port else [port]
        if len(ports) > 1:
            raise PicoError(f"{len(ports)} Picos found; select one explicitly")
        if ports:
            try:
                remaining = max(0.05, min(1.0, deadline - clock()))
                with open_link(ports[0], remaining) as link:
                    if hasattr(link, "reset_input_buffer"):
                        link.reset_input_buffer()
                    caps = PicoClient(link, timeout=remaining, clock=clock).negotiate()
                    if caps.get("proto") != "2":
                        raise PicoProtocolError(f"unexpected protocol {caps.get('proto')!r}")
                    return ports[0], caps
            except (OSError, PicoTimeout, PicoProtocolError) as exc:
                last_error = exc
        if clock() < deadline:
            sleep(min(0.2, max(0, deadline - clock())))
    raise PicoTimeout(f"Pico v2 not ready within {timeout}s: {last_error}")
