from datetime import datetime, timezone
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

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
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrixSensor(c, vid, field) for vid in c.data for field in FIELDS])

class StrixSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, vid, field):
        super().__init__(coordinator)
        self.vid, self.field = vid, field
        self._attr_unique_id = vid + "_" + field
        self._attr_name = FIELDS[field][0]
        self._attr_native_unit_of_measurement = FIELDS[field][1]
        if field == "last_gps_update":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif field in ("mileage", "read_odometer"):
            self._attr_device_class = SensorDeviceClass.DISTANCE
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING if field == "read_odometer" else None
        if field in ("mileage_correction", "gps_age"):
            self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self):
        info = (self.coordinator.data.get(self.vid) or {}).get("info") or {}
        return {"identifiers": {(DOMAIN, self.vid)}, "name": info.get("label") or "Strix vehicle"}

    @property
    def native_value(self):
        vehicle = self.coordinator.data.get(self.vid) or {}
        state = vehicle.get("state") or {}
        if self.field in ("last_gps_update", "gps_age"):
            ts = (((vehicle.get("metadata") or {}).get("state") or {}).get("location") or {}).get("timestamp")
            if not isinstance(ts, (int, float)) or ts <= 0:
                return None
            when = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            if self.field == "last_gps_update":
                return when
            return max(0, round((datetime.now(timezone.utc) - when).total_seconds() / 60, 1))
        return state.get(self.field)

    @property
    def extra_state_attributes(self):
        vehicle = self.coordinator.data.get(self.vid) or {}
        if self.field == "mileage":
            return {"source": "Strix vehicle configuration (user-entered)"}
        if self.field == "read_odometer":
            return {"interpretation": "GPS cumulative distance suspected; not verified"}
        return {}
