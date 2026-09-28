"""Base entity for JuiceBox Local."""

from datetime import timedelta
from typing import override

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import utcnow

from .const import AVAILABILITY_TIMEOUT_SECONDS, DOMAIN
from .coordinator import JuiceBoxCoordinator


class JuiceBoxEntity(CoordinatorEntity[JuiceBoxCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: JuiceBoxCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"

    @property
    @override
    def device_info(self) -> DeviceInfo:
        state = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            manufacturer="Enel X / eMotorWerks",
            model="JuiceBox",
            name="JuiceBox",
            serial_number=state.serial,
        )

    @property
    @override
    def available(self) -> bool:
        last_seen = self.coordinator.data.last_seen
        return last_seen is not None and utcnow() - last_seen < timedelta(
            seconds=AVAILABILITY_TIMEOUT_SECONDS
        )
