"""Push coordinator for JuiceBox Local."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT, DOMAIN
from .gateway import JuiceBoxGateway
from .models import JuiceBoxState

_LOGGER = logging.getLogger(__name__)
type JuiceBoxConfigEntry = ConfigEntry["JuiceBoxCoordinator"]


class JuiceBoxCoordinator(DataUpdateCoordinator[JuiceBoxState]):
    """Own the UDP gateway and publish push updates."""

    config_entry: JuiceBoxConfigEntry

    def __init__(self, hass: HomeAssistant, entry: JuiceBoxConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.data = JuiceBoxState()
        self.gateway = JuiceBoxGateway(
            entry.data[CONF_HOST],
            entry.data.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
            self._handle_state,
        )

    async def async_start(self) -> None:
        await self.gateway.async_start()

    async def async_stop(self) -> None:
        await self.gateway.async_stop()

    @callback
    def _handle_state(self, state: JuiceBoxState) -> None:
        self.async_set_updated_data(state)

    async def async_set_online_current(self, value: int) -> None:
        self.gateway.set_online_current(value)

    async def async_set_offline_current(self, value: int) -> None:
        self.gateway.set_offline_current(value)
