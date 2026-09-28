"""JuiceBox legacy UDP protocol parser and command builder."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from .crc import JuiceBoxCRC
from .exceptions import JuiceBoxInvalidMessageFormat

STATUS = {0: "Unplugged", 1: "Plugged In", 2: "Charging", 5: "Error"}
BASE_RE = re.compile(r"^(?P<serial>[0-9]+):(?P<version>v[0-9]+[eu]?)")
OLD_RE = re.compile(r"^(?P<serial>[0-9]+):(?P<data>.*)")
PAYLOAD_RE = re.compile(r"(?P<payload>[^!]*)(?:!(?P<crc>[A-Z0-9]{3}))?[:$]$")
PART_RE = re.compile(r"(?:(?P<serial>[0-9]+):)?[,]?(?P<key>[A-Za-z]+)(?P<value>-?[0-9]+[u]?)")

ALIASES = {
    "A": "current", "C": "current_max_offline", "E": "energy_session",
    "f": "frequency", "i": "interval", "m": "current_rating",
    "M": "current_max_online", "L": "energy_lifetime", "p": "power_factor",
    "s": "counter", "S": "status", "t": "report_time", "T": "temperature",
    "u": "loop_counter", "v": "protocol_version", "V": "voltage",
}


def _process(key: str, value: str | None, values: dict[str, str]) -> Any:
    if value is None:
        return None
    if key == "A":
        return round(float(value) * 0.1, 1)
    if key == "V":
        return float(value) if len(value) < 4 else round(float(value) * 0.1, 1)
    if key == "T":
        return round(float(value) * 1.8 + 32, 2)
    if key == "f":
        return round(float(value) * 0.01, 2)
    if key == "p":
        return round(float(value) * 0.001, 3)
    if key in {"C", "E", "i", "m", "M", "L"}:
        return int(value)
    if key == "S":
        if value.isnumeric() and int(value) in STATUS:
            return STATUS[int(value)]
        current = values.get("A")
        if current and current.isnumeric():
            return "Plugged In" if int(current) == 0 else "Charging"
        return f"unknown {value}"
    return value


class JuiceBoxStatusMessage:
    """Decoded status datagram."""

    def __init__(self, raw: str, has_crc: bool) -> None:
        self.raw = raw
        self.has_crc = has_crc
        self.values: dict[str, str] = {}
        self.payload_str: str | None = None
        self.crc_str: str | None = None
        self._parse()

    def _parse(self) -> None:
        match = PAYLOAD_RE.search(self.raw)
        if not match:
            raise JuiceBoxInvalidMessageFormat(f"Unable to parse message: {self.raw!r}")
        self.payload_str = match.group("payload")
        self.crc_str = match.group("crc")
        if self.has_crc:
            expected = JuiceBoxCRC(self.payload_str).base35()
            if self.crc_str != expected:
                raise JuiceBoxInvalidMessageFormat(
                    f"Invalid CRC: expected {expected}, got {self.crc_str}"
                )
        elif self.crc_str:
            raise JuiceBoxInvalidMessageFormat("Unexpected CRC")

        remaining = self.payload_str
        while remaining:
            part = PART_RE.match(remaining)
            if not part:
                break
            if part.group("serial"):
                self.values["serial"] = part.group("serial")
            key = part.group("key")
            if key not in self.values:
                self.values[key] = part.group("value")
            remaining = remaining[len(part.group(0)):]

    def get_value(self, key: str) -> str | None:
        if key in self.values:
            return self.values[key]
        for raw, alias in ALIASES.items():
            if alias == key:
                return self.values.get(raw)
        return None

    def to_simple_format(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": "basic", "current": 0.0, "energy_session": 0}
        if "serial" in self.values:
            data["serial"] = self.values["serial"]
        for key, value in self.values.items():
            if key == "serial":
                continue
            alias = ALIASES.get(key, key)
            data[alias] = _process(key, value, self.values)
        if "voltage" in data:
            data["power"] = round(float(data["voltage"]) * float(data.get("current", 0)))
        return data


class JuiceBoxDebugMessage:
    """Decoded debug datagram."""

    def __init__(self, raw: str) -> None:
        match = OLD_RE.match(raw.rstrip(":"))
        if not match:
            raise JuiceBoxInvalidMessageFormat("Invalid debug message")
        text = re.sub(r"^DBG,", "", match.group("data"))
        prefix = text[:4]
        level = {"NFO:": "INFO", "WRN:": "WARNING", "ERR:": "ERROR"}.get(prefix, prefix)
        body = text[4:]
        self.values = {
            "type": "debug",
            "serial": match.group("serial"),
            "debug_message": f"{level}: {body}",
            "boot": body.startswith("BOT:"),
        }

    def to_simple_format(self) -> dict[str, Any]:
        return dict(self.values)


class JuiceBoxEncryptedMessage:
    """Encrypted message placeholder."""

    def __init__(self, serial: str | None = None, version: str | None = None) -> None:
        self.serial = serial
        self.version = version


class JuiceBoxCommand:
    """Command response sent to a JuiceBox."""

    def __init__(self, previous: JuiceBoxCommand | None = None, new_version: bool = False) -> None:
        self.new_version = new_version
        self.command = 6
        self.counter = 1 if previous is None or previous.counter >= 999 else previous.counter + 1
        self.offline_amperage = 0 if previous is None else previous.offline_amperage
        self.instant_amperage = 0 if previous is None else previous.instant_amperage
        self.time = datetime.today()

    def build(self) -> str:
        payload = f"CMD{self.time.strftime('%w%H%M')}"
        if self.new_version:
            payload += f"A{self.instant_amperage:04d}M{self.offline_amperage:03d}"
        else:
            payload += f"A{self.instant_amperage:02d}M{self.offline_amperage:02d}"
        payload += f"C{self.command:03d}S{self.counter:03d}"
        return f"{payload}!{JuiceBoxCRC(payload).base35()}$"


def juicebox_message_from_bytes(data: bytes) -> JuiceBoxStatusMessage | JuiceBoxDebugMessage | JuiceBoxEncryptedMessage:
    """Decode a JuiceBox UDP datagram."""
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError:
        prefix = data[:33].decode("utf-8", errors="ignore")
        match = BASE_RE.match(prefix)
        if match:
            return JuiceBoxEncryptedMessage(match.group("serial"), match.group("version"))
        raise JuiceBoxInvalidMessageFormat("Unable to decode JuiceBox message")

    match = BASE_RE.match(raw)
    if match:
        version = match.group("version")
        if version in {"v09e", "v08"}:
            return JuiceBoxEncryptedMessage(match.group("serial"), version)
        return JuiceBoxStatusMessage(raw, has_crc=True)

    match = OLD_RE.match(raw)
    if match:
        if match.group("data").startswith("DBG"):
            return JuiceBoxDebugMessage(raw)
        return JuiceBoxStatusMessage(raw, has_crc=False)

    raise JuiceBoxInvalidMessageFormat(f"Unsupported JuiceBox message: {raw!r}")
