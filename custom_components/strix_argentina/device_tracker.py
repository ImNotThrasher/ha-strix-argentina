from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrixTracker(c, vid) for vid in c.data])

class StrixTracker(CoordinatorEntity, TrackerEntity):
    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator, vid):
        super().__init__(coordinator)
        self.vid = vid
        self._attr_unique_id = vid + "_location"

    @property
    def device_info(self):
        info = (self.coordinator.data.get(self.vid) or {}).get("info") or {}
        return {"identifiers": {(DOMAIN, self.vid)}, "name": info.get("label") or "Strix vehicle", "manufacturer": info.get("make") or "Strix", "model": info.get("model") or "Vehicle", "serial_number": self.vid}

    @property
    def latitude(self):
        coords = ((((self.coordinator.data.get(self.vid) or {}).get("state") or {}).get("location") or {}).get("coordinates") or [])
        return float(coords[0]) if len(coords) >= 2 else None

    @property
    def longitude(self):
        coords = ((((self.coordinator.data.get(self.vid) or {}).get("state") or {}).get("location") or {}).get("coordinates") or [])
        return float(coords[1]) if len(coords) >= 2 else None

    @property
    def available(self):
        return super().available and self.vid in self.coordinator.data and self.latitude is not None

    @property
    def extra_state_attributes(self):
        v = self.coordinator.data.get(self.vid) or {}
        info = v.get("info") or {}
        attrs = {"last_gps_timestamp_ms": (((v.get("metadata") or {}).get("state") or {}).get("location") or {}).get("timestamp"), "vehicle_year": info.get("year"), "vehicle_color": info.get("color"), "vehicle_plate": info.get("domain"), "vehicle_type": info.get("subtype")}
        return {key: value for key, value in attrs.items() if value is not None}
