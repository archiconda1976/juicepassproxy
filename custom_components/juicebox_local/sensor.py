"""Sensor entities for JuiceBox Local."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import JuiceBoxConfigEntry, JuiceBoxCoordinator
from .entity import JuiceBoxEntity
from .models import JuiceBoxState

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JuiceBoxSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[JuiceBoxState], StateType | datetime]


SENSORS = (
    JuiceBoxSensorEntityDescription(key="status", name="Status", icon="mdi:ev-station",
        value_fn=lambda s: s.status),
    JuiceBoxSensorEntityDescription(key="current", name="Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.current),
    JuiceBoxSensorEntityDescription(key="power", name="Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.power),
    JuiceBoxSensorEntityDescription(key="voltage", name="Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.voltage),
    JuiceBoxSensorEntityDescription(key="energy_session", name="Session energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL, value_fn=lambda s: s.energy_session),
    JuiceBoxSensorEntityDescription(key="energy_lifetime", name="Lifetime energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda s: s.energy_lifetime),
    JuiceBoxSensorEntityDescription(key="temperature", name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.temperature),
    JuiceBoxSensorEntityDescription(key="frequency", name="Frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT, value_fn=lambda s: s.frequency),
    JuiceBoxSensorEntityDescription(key="current_rating", name="Current rating",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.current_rating),
    JuiceBoxSensorEntityDescription(key="current_max_online", name="Online current limit reported",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.current_max_online),
    JuiceBoxSensorEntityDescription(key="current_max_offline", name="Offline current limit reported",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.current_max_offline),
    JuiceBoxSensorEntityDescription(key="protocol_version", name="Protocol version",
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.protocol_version),
    JuiceBoxSensorEntityDescription(key="debug_message", name="Last debug message",
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.debug_message),
    JuiceBoxSensorEntityDescription(key="last_seen", name="Last seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=lambda s: s.last_seen),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JuiceBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(JuiceBoxSensor(coordinator, description) for description in SENSORS)


class JuiceBoxSensor(JuiceBoxEntity, SensorEntity):
    entity_description: JuiceBoxSensorEntityDescription

    def __init__(self, coordinator: JuiceBoxCoordinator, description: JuiceBoxSensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator.data)
