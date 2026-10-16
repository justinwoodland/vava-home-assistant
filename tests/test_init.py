from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vava_projector.api.http import VolumeInfo
from custom_components.vava_projector.const import DOMAIN


async def test_setup_and_unload_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="1.2.3.4", data={"host": "1.2.3.4"}
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.vava_projector.api.http.VavaHttpClient.async_get_volume",
        AsyncMock(return_value=VolumeInfo(ok=True, current=5)),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        assert entry.entry_id in hass.data[DOMAIN]
        assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.entry_id not in hass.data[DOMAIN]
