# tests/test_volume_parse.py
from custom_components.vava_projector.api.http import parse_volume_response

SAMPLE = "{'status':'ok','action':'get_volume,'currentVolume':'0','maxVolume':'100','mute':'false'}"

def test_parse_malformed_get_volume_sample():
    info = parse_volume_response(SAMPLE)
    assert info.ok is True
    assert info.current == 0
    assert info.max == 100
    assert info.mute is False

def test_parse_quoted_values():
    info = parse_volume_response(
        "{'status':'ok','currentVolume':'12','maxVolume':'100','mute':'true'}"
    )
    assert info.current == 12
    assert info.mute is True

def test_parse_empty_fails():
    info = parse_volume_response("")
    assert info.ok is False
