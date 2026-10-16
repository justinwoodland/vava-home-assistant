"""eShare UDP discovery probe and response parsing."""

from __future__ import annotations

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

DISCOVERY_PORT = 48689


@dataclass(frozen=True)
class DiscoveredDevice:
    name: str
    control_port: int
    speak_port: int | None = None
    raw: str = ""
    host: str = ""


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


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.found: dict[str, DiscoveredDevice] = {}

    def datagram_received(self, data: bytes, addr) -> None:
        text = data.decode("utf-8", errors="ignore").strip("\x00\r\n ")
        # Replies may carry a binary header; locate the payload.
        idx = text.find("ECloudBox")
        if idx < 0:
            return
        dev = parse_discovery_response(text[idx:])
        if dev is None:
            return
        host = addr[0]
        self.found[host] = DiscoveredDevice(
            name=dev.name,
            control_port=dev.control_port,
            speak_port=dev.speak_port,
            raw=dev.raw,
            host=host,
        )

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("Discovery socket error: %s", exc)


async def async_discover(
    timeout: float = 3.0,
    broadcast_address: str = "255.255.255.255",
) -> list[DiscoveredDevice]:
    """Broadcast FindECloudBox and collect ECloudBox replies (host = source IP)."""
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)
    try:
        sock.bind(("", 0))
    except OSError as err:
        sock.close()
        _LOGGER.debug("Discovery bind failed: %s", err)
        return []
    transport, protocol = await loop.create_datagram_endpoint(
        _DiscoveryProtocol, sock=sock
    )
    try:
        transport.sendto(build_find_probe(), (broadcast_address, DISCOVERY_PORT))
        await asyncio.sleep(timeout)
    except OSError as err:
        _LOGGER.debug("Discovery send failed: %s", err)
    finally:
        transport.close()
    return list(protocol.found.values())
