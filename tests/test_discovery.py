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
