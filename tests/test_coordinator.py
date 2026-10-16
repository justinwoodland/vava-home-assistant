from unittest.mock import patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.vava_projector.api.http import VolumeInfo
from custom_components.vava_projector.coordinator import VavaCoordinator, VavaData

MONO = "custom_components.vava_projector.coordinator.time.monotonic"


class FakeHttp:
    def __init__(self):
        self.fail = False
        self.not_ok = False
        self.keys = []
        self.key_fail = False

    async def async_get_volume(self):
        if self.fail:
            raise OSError("down")
        if self.not_ok:
            return VolumeInfo(ok=False)
        return VolumeInfo(ok=True, current=1, max=100, mute=False)

    async def async_send_keycode(self, keycode: int):
        if self.key_fail:
            raise OSError("http down")
        self.keys.append(keycode)


class FakeTcp:
    def __init__(self, fail=False):
        self.fail = fail
        self.attempts = []
        self.keys = []

    async def async_send_keyevent(self, keycode: int):
        self.attempts.append(keycode)
        if self.fail:
            raise OSError("tcp down")
        self.keys.append(keycode)


def make(hass, tcp_fail=False):
    http, tcp = FakeHttp(), FakeTcp(fail=tcp_fail)
    coord = VavaCoordinator(
        hass, http=http, tcp=tcp, poll_interval=10, shutdown_grace=15
    )
    return coord, http, tcp


async def test_update_success(hass):
    coord, _, _ = make(hass)
    data = await coord._async_update_data()
    assert data == VavaData(
        available=True,
        volume=VolumeInfo(ok=True, current=1, max=100, mute=False),
        powering_off_until=None,
    )


async def test_update_failure_without_grace_unavailable(hass):
    coord, http, _ = make(hass)
    http.fail = True
    data = await coord._async_update_data()
    assert data.available is False
    assert data.volume is None


async def test_update_not_ok_response_is_failure(hass):
    coord, http, _ = make(hass)
    http.not_ok = True
    data = await coord._async_update_data()
    assert data.available is False


async def test_send_key_uses_tcp_first(hass):
    coord, http, tcp = make(hass)
    await coord.async_send_key("VOLUME_UP")
    assert tcp.keys == [24]
    assert http.keys == []


async def test_send_key_falls_back_to_http(hass):
    coord, http, tcp = make(hass, tcp_fail=True)
    await coord.async_send_key("VOLUME_UP")
    assert tcp.attempts == [24]
    assert http.keys == [24]


async def test_send_key_both_fail_raises(hass):
    coord, http, _ = make(hass, tcp_fail=True)
    http.key_fail = True
    with pytest.raises(HomeAssistantError):
        await coord.async_send_key("OK")


async def test_send_key_unknown_raises(hass):
    coord, http, tcp = make(hass)
    with pytest.raises(HomeAssistantError):
        await coord.async_send_key("NOPE")
    assert tcp.attempts == [] and http.keys == []


async def test_power_uses_tcp_203(hass):
    coord, http, tcp = make(hass)
    await coord.async_send_key("POWER")
    assert tcp.keys == [203]
    assert http.keys == []


async def test_power_falls_back_to_http_26(hass):
    coord, http, tcp = make(hass, tcp_fail=True)
    await coord.async_send_key("POWER")
    assert tcp.attempts == [203]
    assert http.keys == [26]
    assert coord.powering_off_until is not None


async def test_power_failure_does_not_start_grace(hass):
    coord, http, _ = make(hass, tcp_fail=True)
    http.key_fail = True
    with pytest.raises(HomeAssistantError):
        await coord.async_send_key("POWER")
    assert coord.powering_off_until is None


async def test_non_power_key_does_not_start_grace(hass):
    coord, _, _ = make(hass)
    await coord.async_send_key("OK")
    assert coord.powering_off_until is None


async def test_power_sets_grace_deadline(hass):
    coord, _, _ = make(hass)
    with patch(MONO, return_value=1000.0):
        await coord.async_send_key("POWER")
    assert coord.powering_off_until == 1015.0


async def test_grace_keeps_available_after_power_off(hass):
    coord, http, _ = make(hass)
    with patch(MONO, return_value=1000.0):
        await coord.async_send_key("POWER")
        await coord._async_update_data()  # healthy poll caches volume
        http.fail = True
    with patch(MONO, return_value=1005.0):
        data = await coord._async_update_data()
    assert data.available is True
    assert data.volume == VolumeInfo(ok=True, current=1, max=100, mute=False)
    assert data.powering_off_until == 1015.0


async def test_grace_expired_marks_unavailable(hass):
    coord, http, _ = make(hass)
    with patch(MONO, return_value=1000.0):
        await coord.async_send_key("POWER")
        http.fail = True
    with patch(MONO, return_value=1016.0):
        data = await coord._async_update_data()
    assert data.available is False
    assert data.volume is None
    assert data.powering_off_until is None


async def test_grace_with_no_prior_data(hass):
    coord, http, _ = make(hass)
    with patch(MONO, return_value=1000.0):
        await coord.async_send_key("POWER")
        http.fail = True
        data = await coord._async_update_data()
    assert data.available is True
    assert data.volume is None


async def test_poll_success_after_grace_clears_deadline(hass):
    coord, _, _ = make(hass)
    with patch(MONO, return_value=1000.0):
        await coord.async_send_key("POWER")
    with patch(MONO, return_value=1020.0):
        data = await coord._async_update_data()
    assert data.available is True
    assert data.powering_off_until is None
