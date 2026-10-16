from custom_components.vava_projector.const import KEYCODES, DOMAIN


def test_domain():
    assert DOMAIN == "vava_projector"


def test_power_keycode_is_app_wire_value():
    assert KEYCODES["POWER"] == 203


def test_volume_and_nav_keycodes():
    assert KEYCODES["VOLUME_UP"] == 24
    assert KEYCODES["VOLUME_DOWN"] == 25
    assert KEYCODES["UP"] == 19
    assert KEYCODES["OK"] == 66
    assert KEYCODES["HOME"] == 3
