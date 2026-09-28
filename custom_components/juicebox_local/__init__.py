"""The JuiceBox Local integration."""

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import PLATFORMS
from .coordinator import JuiceBoxConfigEntry, JuiceBoxCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: JuiceBoxConfigEntry) -> bool:
    coordinator = JuiceBoxCoordinator(hass, entry)
    try:
        await coordinator.async_start()
    except OSError as err:
        raise ConfigEntryNotReady(f"Unable to bind JuiceBox UDP listener: {err}") from err
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JuiceBoxConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded
