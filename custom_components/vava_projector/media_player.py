"""Media player platform for the VAVA projector."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN
from .coordinator import VavaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VavaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VavaProjectorMediaPlayer(coordinator, entry)])


class VavaProjectorMediaPlayer(CoordinatorEntity[VavaCoordinator], MediaPlayerEntity):
    """Power-off and volume-step control; power-on is not possible over the network."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.VOLUME_STEP
    )

    def __init__(self, coordinator: VavaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]
        self._attr_unique_id = host
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            name=entry.title,
            manufacturer="VAVA",
        )

    @property
    def state(self) -> MediaPlayerState:
        if self.coordinator.data.available:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        volume = self.coordinator.data.volume
        if volume is None or not volume.ok or volume.max <= 0:
            return None
        return volume.current / volume.max

    async def async_turn_on(self) -> None:
        """The projector cannot be woken over the network; intentionally a no-op."""

    async def async_turn_off(self) -> None:
        await self.coordinator.async_send_key("POWER")

    async def async_volume_up(self) -> None:
        await self.coordinator.async_send_key("VOLUME_UP")

    async def async_volume_down(self) -> None:
        await self.coordinator.async_send_key("VOLUME_DOWN")
