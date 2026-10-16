"""Tests for eShare UDP discovery probe and response parser."""

from custom_components.vava_projector.api.discovery import (
    build_find_probe,
    parse_discovery_response,
)


def test_build_find_probe_contains_find_ecloud_box():
    pkt = build_find_probe()
    assert len(pkt) == 50
    assert b"FindECloudBox" in pkt


def test_parse_ecloudbox516():
    text = "ECloudBox516:VAVA-6720:8121:25123:56789:sn=0x001f:6"
    dev = parse_discovery_response(text)
    assert dev is not None
    assert dev.name == "VAVA-6720"
    assert dev.control_port == 8121
    assert dev.speak_port == 25123


def test_parse_rejects_garbage():
    assert parse_discovery_response("hello") is None


async def test_async_discover_collects_reply_with_source_ip(socket_enabled):
    import asyncio

    from custom_components.vava_projector.api import discovery

    class Responder(asyncio.DatagramProtocol):
        def connection_made(self, transport):
            self.transport = transport

        def datagram_received(self, data, addr):
            if b"FindECloudBox" in data:
                self.transport.sendto(
                    b"ECloudBox516:VAVA-6720:8121:25123:56789:sn=0x001f:6", addr
                )

    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        Responder, local_addr=("127.0.0.1", 0)
    )
    port = transport.get_extra_info("sockname")[1]
    try:
        orig = discovery.DISCOVERY_PORT
        discovery.DISCOVERY_PORT = port
        try:
            devices = await discovery.async_discover(
                timeout=0.3, broadcast_address="127.0.0.1"
            )
        finally:
            discovery.DISCOVERY_PORT = orig
    finally:
        transport.close()
    assert len(devices) == 1
    assert devices[0].host == "127.0.0.1"
    assert devices[0].name == "VAVA-6720"
