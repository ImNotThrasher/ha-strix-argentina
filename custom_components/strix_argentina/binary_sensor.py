"""Binary status sensors for Strix vehicles."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .helpers import device_info, vehicle_state

# Field names are part of existing unique IDs; do not rename them.
FIELDS = {
    "contact_on": "Ignition",
    "in_motion": "In motion",
    "towing": "Towing detected",
    "fuel_cut_off": "Fuel cut off",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create binary sensors for vehicles present during initial setup."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StrixBinary(coordinator, vid, field)
            for vid in coordinator.data
            for field in FIELDS
        ]
    )


class StrixBinary(CoordinatorEntity, BinarySensorEntity):
    """Expose one boolean state reported by Strix."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, vid, field):
        super().__init__(coordinator)
        self.vid = vid
        self.field = field
        self._attr_unique_id = vid + "_" + field
        self._attr_name = FIELDS[field]

    @property
    def device_info(self):
        vehicle = self.coordinator.data.get(self.vid) or {}
        return device_info(vehicle, self.vid)

    @property
    def is_on(self):
        vehicle = self.coordinator.data.get(self.vid) or {}
        return vehicle_state(vehicle).get(self.field)
