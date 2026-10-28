"""GPS tracking entities for Strix vehicles."""

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .helpers import device_info, gps_coordinates, gps_timestamp_ms, vehicle_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Create one GPS tracker per vehicle in the initial API response."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StrixTracker(coordinator, vid) for vid in coordinator.data])


class StrixTracker(CoordinatorEntity, TrackerEntity):
    """Expose the last reported GPS position for a vehicle."""

    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator, vid):
        super().__init__(coordinator)
        self.vid = vid
        self._attr_unique_id = vid + "_location"

    @property
    def _vehicle(self):
        return self.coordinator.data.get(self.vid) or {}

    @property
    def device_info(self):
        return device_info(self._vehicle, self.vid, detailed=True)

    @property
    def latitude(self):
        coordinates = gps_coordinates(self._vehicle)
        return float(coordinates[0]) if len(coordinates) >= 2 else None

    @property
    def longitude(self):
        coordinates = gps_coordinates(self._vehicle)
        return float(coordinates[1]) if len(coordinates) >= 2 else None

    @property
    def available(self):
        return (
            super().available
            and self.vid in self.coordinator.data
            and self.latitude is not None
        )

    @property
    def extra_state_attributes(self):
        info = vehicle_info(self._vehicle)
        attributes = {
            "last_gps_timestamp_ms": gps_timestamp_ms(self._vehicle),
            "vehicle_year": info.get("year"),
            "vehicle_color": info.get("color"),
            "vehicle_plate": info.get("domain"),
            "vehicle_type": info.get("subtype"),
        }
        return {key: value for key, value in attributes.items() if value is not None}
