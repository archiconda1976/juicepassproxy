"""Writable charging-current limits for JuiceBox Local."""

from typing import override

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.const import EntityCategory, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import JuiceBoxConfigEntry, JuiceBoxCoordinator
from .entity import JuiceBoxEntity

PARALLEL_UPDATES = 0

ONLINE = NumberEntityDescription(
    key="desired_online_current", name="Online current limit",
    device_class=NumberDeviceClass.CURRENT,
    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    entity_category=EntityCategory.CONFIG,
)
OFFLINE = NumberEntityDescription(
    key="desired_offline_current", name="Offline current limit",
    device_class=NumberDeviceClass.CURRENT,
    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JuiceBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities((
        JuiceBoxCurrentNumber(coordinator, ONLINE, True),
        JuiceBoxCurrentNumber(coordinator, OFFLINE, False),
    ))


class JuiceBoxCurrentNumber(JuiceBoxEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_step = 1

    def __init__(self, coordinator: JuiceBoxCoordinator, description: NumberEntityDescription, online: bool) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._online = online

    @property
    @override
    def native_max_value(self) -> float:
        return float(self.coordinator.data.current_rating or 80)

    @property
    @override
    def native_value(self) -> float | None:
        value = (
            self.coordinator.data.desired_online_current
            if self._online else self.coordinator.data.desired_offline_current
        )
        return float(value) if value is not None else None

    @override
    async def async_set_native_value(self, value: float) -> None:
        if self._online:
            await self.coordinator.async_set_online_current(int(value))
        else:
            await self.coordinator.async_set_offline_current(int(value))
