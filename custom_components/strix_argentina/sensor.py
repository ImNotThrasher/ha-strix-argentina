"""Numeric and timestamp sensors for Strix vehicles."""

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from .entity import StrixEntity
from .discovery import register_vehicle_discovery

from .const import DOMAIN
from .helpers import device_info, gps_timestamp_ms, vehicle_state

# Keep field names stable: they form part of existing entity unique IDs.
FIELDS = {
    "speed": ("Speed", "km/h"),
    "heading": ("Heading", "°"),
    "mileage": ("Declared mileage", "km"),
    "read_odometer": ("Strix GPS distance (unverified)", "km"),
    "mileage_correction": ("Mileage correction", None),
    "last_gps_update": ("Last GPS update", None),
    "gps_age": ("GPS data age", "min"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create sensors for vehicles present during initial setup."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    register_vehicle_discovery(hass, entry, coordinator, async_add_entities,
        lambda vid: [StrixSensor(coordinator, vid, field) for field in FIELDS])


class StrixSensor(StrixEntity, SensorEntity):
    """Expose one field from a Strix vehicle's latest state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, vid, field):
        super().__init__(coordinator, vid)
        self.field = field
        self._attr_unique_id = vid + "_" + field
        self._attr_name, self._attr_native_unit_of_measurement = FIELDS[field]

        if field == "last_gps_update":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif field in ("mileage", "read_odometer"):
            self._attr_device_class = SensorDeviceClass.DISTANCE
            self._attr_state_class = (
                SensorStateClass.TOTAL_INCREASING
                if field == "read_odometer"
                else None
            )

        if field in ("mileage_correction", "gps_age"):
            self._attr_entity_registry_enabled_default = False

    @property
    def _vehicle(self):
        return self.vehicle

    @property
    def device_info(self):
        return device_info(self._vehicle, self.vid)

    @property
    def native_value(self):
        if self.field in ("last_gps_update", "gps_age"):
            timestamp = gps_timestamp_ms(self._vehicle)
            if not isinstance(timestamp, (int, float)) or timestamp <= 0:
                return None

            when = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            if self.field == "last_gps_update":
                return when
            return max(
                0,
                round((datetime.now(timezone.utc) - when).total_seconds() / 60, 1),
            )

        return vehicle_state(self._vehicle).get(self.field)

    @property
    def extra_state_attributes(self):
        if self.field == "mileage":
            return {"source": "Strix vehicle configuration (user-entered)"}
        if self.field == "read_odometer":
            return {"interpretation": "GPS cumulative distance suspected; not verified"}
        return {}
