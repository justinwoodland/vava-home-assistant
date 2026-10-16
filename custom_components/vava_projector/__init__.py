"""The VAVA projector integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.http import VavaHttpClient
from .api.tcp import VavaTcpClient
from .const import (
    CONF_HOST,
    CONF_HTTP_PORT,
    CONF_POLL_INTERVAL,
    CONF_SHUTDOWN_GRACE,
    CONF_TCP_PORT,
    DEFAULT_HTTP_PORT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SHUTDOWN_GRACE,
    DEFAULT_TCP_PORT,
    DOMAIN,
)
from .coordinator import VavaCoordinator

PLATFORMS = ["media_player", "remote"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    session = async_get_clientsession(hass)
    http = VavaHttpClient(session, host, entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT))
    tcp = VavaTcpClient(host, entry.data.get(CONF_TCP_PORT, DEFAULT_TCP_PORT))
    coordinator = VavaCoordinator(
        hass,
        http=http,
        tcp=tcp,
        poll_interval=entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        shutdown_grace=entry.options.get(CONF_SHUTDOWN_GRACE, DEFAULT_SHUTDOWN_GRACE),
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
