"""eShare UDP discovery probe and response parsing."""

from __future__ import annotations

import struct
from dataclasses import dataclass

DISCOVERY_PORT = 48689


@dataclass(frozen=True)
class DiscoveredDevice:
    name: str
    control_port: int
    speak_port: int | None = None
    raw: str = ""


def build_find_probe() -> bytes:
    msg = b"FindECloudBox"
    buf = bytearray(50)
    struct.pack_into(">IIIII", buf, 0, 0, 0, 0, len(msg), 0)
    buf[20 : 20 + len(msg)] = msg
    return bytes(buf)


def parse_discovery_response(text: str) -> DiscoveredDevice | None:
    if not text.startswith("ECloudBox"):
        return None
    parts = text.split(":")
    if len(parts) < 3:
        return None
    try:
        name = parts[1]
        control_port = int(parts[2])
        speak_port = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None
    except (ValueError, IndexError):
        return None
    return DiscoveredDevice(
        name=name, control_port=control_port, speak_port=speak_port, raw=text
    )
