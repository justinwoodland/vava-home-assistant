from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.http import VavaHttpClient, VolumeInfo
from .api.tcp import VavaTcpClient
from .const import (
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SHUTDOWN_GRACE,
    DOMAIN,
    HTTP_POWER_KEYCODE,
    KEYCODES,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VavaData:
    available: bool
    volume: VolumeInfo | None = None
    powering_off_until: float | None = None


class VavaCoordinator(DataUpdateCoordinator[VavaData]):
    """Polls projector volume (availability signal) and sends key events."""

    def __init__(
        self,
        hass: HomeAssistant,
        http: VavaHttpClient,
        tcp: VavaTcpClient,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        shutdown_grace: int = DEFAULT_SHUTDOWN_GRACE,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self._http = http
        self._tcp = tcp
        self._shutdown_grace = shutdown_grace
        self.powering_off_until: float | None = None
        self._last_volume: VolumeInfo | None = None

    async def _async_update_data(self) -> VavaData:
        now = time.monotonic()
        try:
            volume = await self._http.async_get_volume()
            if not volume.ok:
                raise ValueError("volume response not ok")
        except Exception as err:  # noqa: BLE001 - any failure means unreachable
            _LOGGER.debug("Volume poll failed: %s", err)
            if self.powering_off_until is not None and now < self.powering_off_until:
                return VavaData(
                    available=True,
                    volume=self._last_volume,
                    powering_off_until=self.powering_off_until,
                )
            self.powering_off_until = None
            self._last_volume = None
            return VavaData(available=False, volume=None, powering_off_until=None)

        self._last_volume = volume
        if self.powering_off_until is not None and now >= self.powering_off_until:
            self.powering_off_until = None
        return VavaData(
            available=True,
            volume=volume,
            powering_off_until=self.powering_off_until,
        )

    async def async_send_key(self, name: str) -> None:
        """Send a named key: TCP first, one HTTP keycode fallback."""
        try:
            tcp_code = KEYCODES[name]
        except KeyError as err:
            raise HomeAssistantError(f"Unknown key: {name}") from err
        http_code = HTTP_POWER_KEYCODE if name == "POWER" else tcp_code

        try:
            await self._tcp.async_send_keyevent(tcp_code)
        except Exception as tcp_err:  # noqa: BLE001
            _LOGGER.debug("TCP key %s failed (%s); falling back to HTTP", name, tcp_err)
            try:
                await self._http.async_send_keycode(http_code)
            except Exception as http_err:  # noqa: BLE001
                raise HomeAssistantError(
                    f"Failed to send key {name} via TCP and HTTP"
                ) from http_err

        if name == "POWER":
            self.powering_off_until = time.monotonic() + self._shutdown_grace
