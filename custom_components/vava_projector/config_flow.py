"""Config flow for the VAVA projector integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .api.discovery import DiscoveredDevice, async_discover
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

CONF_DEVICE = "device"
DEFAULT_NAME = "VAVA Projector"

_PORT = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


class VavaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VAVA projector."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, DiscoveredDevice] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return VavaOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose between discovery and manual entry."""
        return self.async_show_menu(step_id="user", menu_options=["discover", "manual"])

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manual host/port entry."""
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            data = {
                CONF_HOST: host,
                CONF_HTTP_PORT: user_input.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT),
                CONF_TCP_PORT: user_input.get(CONF_TCP_PORT, DEFAULT_TCP_PORT),
                CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
            }
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_HTTP_PORT, default=DEFAULT_HTTP_PORT): _PORT,
                vol.Optional(CONF_TCP_PORT, default=DEFAULT_TCP_PORT): _PORT,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema)

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Discover projectors via UDP and let the user pick one."""
        if user_input is not None:
            device = self._discovered[user_input[CONF_DEVICE]]
            await self.async_set_unique_id(device.host)
            self._abort_if_unique_id_configured()
            data = {
                CONF_HOST: device.host,
                CONF_HTTP_PORT: DEFAULT_HTTP_PORT,
                CONF_TCP_PORT: device.control_port or DEFAULT_TCP_PORT,
                CONF_NAME: device.name or DEFAULT_NAME,
            }
            return self.async_create_entry(title=data[CONF_NAME], data=data)

        devices = await async_discover()
        configured = {
            entry.unique_id for entry in self._async_current_entries(include_ignore=False)
        }
        self._discovered = {
            dev.host: dev for dev in devices if dev.host and dev.host not in configured
        }
        if not self._discovered:
            return self.async_show_form(
                step_id="discover_retry",
                errors={"base": "no_devices_found"},
            )

        options = {
            host: f"{dev.name} ({host})" for host, dev in self._discovered.items()
        }
        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(options)}),
        )

    async def async_step_discover_retry(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Nothing found: go back to the method menu."""
        return await self.async_step_user()


class VavaOptionsFlow(OptionsFlow):
    """Options: polling interval, shutdown grace, ports."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        entry = self.config_entry
        opts = entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLL_INTERVAL,
                    default=opts.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=3600)),
                vol.Required(
                    CONF_SHUTDOWN_GRACE,
                    default=opts.get(CONF_SHUTDOWN_GRACE, DEFAULT_SHUTDOWN_GRACE),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
