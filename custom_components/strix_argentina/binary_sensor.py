from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

FIELDS = {"contact_on": "Ignition", "in_motion": "In motion", "towing": "Towing detected", "fuel_cut_off": "Fuel cut off"}

async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrixBinary(c, vid, field) for vid in c.data for field in FIELDS])

class StrixBinary(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, vid, field):
        super().__init__(coordinator)
        self.vid, self.field = vid, field
        self._attr_unique_id = vid + "_" + field
        self._attr_name = FIELDS[field]
    @property
    def device_info(self):
        info = (self.coordinator.data.get(self.vid) or {}).get("info") or {}
        return {"identifiers": {(DOMAIN, self.vid)}, "name": info.get("label") or "Strix vehicle"}
    @property
    def is_on(self):
        return ((self.coordinator.data.get(self.vid) or {}).get("state") or {}).get(self.field)
