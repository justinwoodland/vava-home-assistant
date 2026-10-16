from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vava_projector.api.http import VolumeInfo
from custom_components.vava_projector.const import DOMAIN
from custom_components.vava_projector.coordinator import VavaData
from custom_components.vava_projector.media_player import (
    VavaProjectorMediaPlayer,
    async_setup_entry,
)


def _make(data: VavaData):
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.async_send_key = AsyncMock()
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="1.2.3.4", title="Living Room", data={"host": "1.2.3.4"}
    )
    return VavaProjectorMediaPlayer(coordinator, entry), coordinator


def test_state_on_when_available():
    entity, _ = _make(VavaData(available=True, volume=VolumeInfo(ok=True, current=5)))
    assert entity.state == MediaPlayerState.ON


def test_state_off_when_unavailable():
    entity, _ = _make(VavaData(available=False))
    assert entity.state == MediaPlayerState.OFF


def test_supported_features_turn_off_and_volume_step_only():
    entity, _ = _make(VavaData(available=True))
    expected = MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.VOLUME_STEP
    assert entity.supported_features == expected
    assert not entity.supported_features & MediaPlayerEntityFeature.VOLUME_SET
    assert not entity.supported_features & MediaPlayerEntityFeature.TURN_ON


def test_volume_level_is_current_over_max():
    entity, _ = _make(
        VavaData(available=True, volume=VolumeInfo(ok=True, current=5, max=20))
    )
    assert entity.volume_level == 0.25


def test_volume_level_none_when_unknown():
    entity, _ = _make(VavaData(available=True, volume=None))
    assert entity.volume_level is None


def test_volume_level_none_when_volume_not_ok():
    entity, _ = _make(VavaData(available=True, volume=VolumeInfo(ok=False)))
    assert entity.volume_level is None


def test_volume_level_none_when_max_zero():
    entity, _ = _make(
        VavaData(available=True, volume=VolumeInfo(ok=True, current=0, max=0))
    )
    assert entity.volume_level is None


async def test_turn_off_sends_power():
    entity, coordinator = _make(VavaData(available=True))
    await entity.async_turn_off()
    coordinator.async_send_key.assert_awaited_once_with("POWER")


async def test_turn_on_is_noop():
    entity, coordinator = _make(VavaData(available=False))
    await entity.async_turn_on()
    coordinator.async_send_key.assert_not_called()


async def test_volume_up_sends_key():
    entity, coordinator = _make(VavaData(available=True))
    await entity.async_volume_up()
    coordinator.async_send_key.assert_awaited_once_with("VOLUME_UP")


async def test_volume_down_sends_key():
    entity, coordinator = _make(VavaData(available=True))
    await entity.async_volume_down()
    coordinator.async_send_key.assert_awaited_once_with("VOLUME_DOWN")


def test_device_info_and_unique_id():
    entity, _ = _make(VavaData(available=True))
    assert entity.unique_id == "1.2.3.4"
    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, "1.2.3.4")}
    assert info["name"] == "Living Room"


async def test_setup_entry_adds_entity(hass):
    coordinator = MagicMock()
    coordinator.data = VavaData(available=True)
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="1.2.3.4", title="Living Room", data={"host": "1.2.3.4"}
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    add = MagicMock()
    await async_setup_entry(hass, entry, add)
    (entities,) = add.call_args.args
    assert len(entities) == 1
    assert isinstance(entities[0], VavaProjectorMediaPlayer)
