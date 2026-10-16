from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vava_projector.api.discovery import DiscoveredDevice
from custom_components.vava_projector.const import DOMAIN

SETUP = "custom_components.vava_projector.async_setup_entry"


async def test_manual_flow_creates_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )
    assert result["type"] is FlowResultType.FORM
    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.1.50"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "192.168.1.50"
    assert result["data"]["http_port"] == 8000
    assert result["data"]["tcp_port"] == 8121
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == "192.168.1.50"


async def test_manual_duplicate_aborts(hass):
    MockConfigEntry(
        domain=DOMAIN, unique_id="192.168.1.50", data={"host": "192.168.1.50"}
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "192.168.1.50"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_discover_flow_selects_device(hass):
    dev = DiscoveredDevice(
        name="VAVA-6720", control_port=8121, speak_port=25123, host="10.0.0.9"
    )
    with patch(
        "custom_components.vava_projector.config_flow.async_discover",
        AsyncMock(return_value=[dev]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "discover"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discover"
    with patch(SETUP, return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"device": "10.0.0.9"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "10.0.0.9"
    assert result["title"] == "VAVA-6720"


async def test_discover_none_found(hass):
    with patch(
        "custom_components.vava_projector.config_flow.async_discover",
        AsyncMock(return_value=[]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "discover"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_devices_found"}


async def test_options_flow(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="1.2.3.4", data={"host": "1.2.3.4"}
    )
    entry.add_to_hass(hass)
    with patch(SETUP, return_value=True):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"poll_interval": 20, "shutdown_grace": 30}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"poll_interval": 20, "shutdown_grace": 30}
