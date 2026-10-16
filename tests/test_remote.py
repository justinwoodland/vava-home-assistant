from unittest.mock import AsyncMock, MagicMock, call

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vava_projector.const import DOMAIN
from custom_components.vava_projector.coordinator import VavaData
from custom_components.vava_projector.remote import VavaProjectorRemote, async_setup_entry


def _make(available: bool = True):
    coordinator = MagicMock()
    coordinator.data = VavaData(available=available)
    coordinator.async_send_key = AsyncMock()
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="1.2.3.4", title="Living Room", data={"host": "1.2.3.4"}
    )
    return VavaProjectorRemote(coordinator, entry), coordinator


async def test_send_command_up_calls_coordinator():
    entity, coordinator = _make()
    await entity.async_send_command(["UP"])
    coordinator.async_send_key.assert_awaited_once_with("UP")


async def test_send_command_accepts_plain_string():
    entity, coordinator = _make()
    await entity.async_send_command("OK")
    coordinator.async_send_key.assert_awaited_once_with("OK")


async def test_send_command_is_case_insensitive():
    entity, coordinator = _make()
    await entity.async_send_command(["home"])
    coordinator.async_send_key.assert_awaited_once_with("HOME")


async def test_send_multiple_commands_in_order():
    entity, coordinator = _make()
    await entity.async_send_command(["DOWN", "DOWN", "OK"])
    assert coordinator.async_send_key.await_args_list == [
        call("DOWN"),
        call("DOWN"),
        call("OK"),
    ]


async def test_num_repeats():
    entity, coordinator = _make()
    await entity.async_send_command(["LEFT"], num_repeats=3)
    assert coordinator.async_send_key.await_count == 3


async def test_unknown_command_raises_without_sending():
    entity, coordinator = _make()
    with pytest.raises(HomeAssistantError):
        await entity.async_send_command(["UP", "NOPE"])
    coordinator.async_send_key.assert_not_called()


def test_is_on_follows_availability():
    assert _make(True)[0].is_on is True
    assert _make(False)[0].is_on is False


def test_activity_list_is_single_remote():
    entity, _ = _make()
    assert entity.activity_list in (None, [], ["Remote"])


def test_unique_id_distinct_from_media_player_and_shared_device():
    entity, _ = _make()
    assert entity.unique_id == "1.2.3.4_remote"
    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, "1.2.3.4")}
    assert info["name"] == "Living Room"
    assert info["manufacturer"] == "VAVA"


async def test_turn_on_off_are_safe():
    entity, coordinator = _make()
    await entity.async_turn_on()
    coordinator.async_send_key.assert_not_called()
    await entity.async_turn_off()
    coordinator.async_send_key.assert_awaited_once_with("POWER")


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
    assert isinstance(entities[0], VavaProjectorRemote)
