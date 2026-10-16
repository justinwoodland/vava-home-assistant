"""Remote platform for the VAVA projector (navigation keys)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import ATTR_NUM_REPEATS, RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN, KEYCODES
from .coordinator import VavaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VavaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VavaProjectorRemote(coordinator, entry)])


class VavaProjectorRemote(CoordinatorEntity[VavaCoordinator], RemoteEntity):
    """Send navigation and volume keys; power-on is not possible over the network."""

    _attr_has_entity_name = True
    _attr_name = "Remote"

    def __init__(self, coordinator: VavaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]
        # media_player uses the bare host as unique_id; keep this one distinct.
        self._attr_unique_id = f"{host}_remote"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name=entry.title,
            manufacturer="VAVA",
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.available)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """The projector cannot be woken over the network; intentionally a no-op."""

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_send_key("POWER")

    async def async_send_command(self, command: Iterable[str] | str, **kwargs: Any) -> None:
        commands = [command] if isinstance(command, str) else list(command)
        names = [name.upper() for name in commands]
        unknown = [name for name in names if name not in KEYCODES]
        if unknown:
            raise HomeAssistantError(
                f"Unknown command(s): {', '.join(unknown)}. "
                f"Valid commands: {', '.join(sorted(KEYCODES))}"
            )
        repeats = max(int(kwargs.get(ATTR_NUM_REPEATS, 1)), 1)
        for _ in range(repeats):
            for name in names:
                await self.coordinator.async_send_key(name)
