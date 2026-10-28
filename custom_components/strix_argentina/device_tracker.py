"""GPS tracking entities for Strix vehicles."""

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from .entity import StrixEntity
from .discovery import register_vehicle_discovery

from .const import DOMAIN
from .helpers import device_info, valid_gps_coordinates, gps_timestamp_ms, vehicle_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Create one GPS tracker per vehicle in the initial API response."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    register_vehicle_discovery(hass, entry, coordinator, async_add_entities,
                               lambda vid: [StrixTracker(coordinator, vid)])


class StrixTracker(StrixEntity, TrackerEntity):
    """Expose the last reported GPS position for a vehicle."""

    _attr_has_entity_name = True
    _attr_name = "Location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator, vid):
        super().__init__(coordinator, vid)
        self._attr_unique_id = vid + "_location"

    @property
    def _vehicle(self):
        return self.vehicle

    @property
    def device_info(self):
        return device_info(self._vehicle, self.vid, detailed=True)

    @property
    def latitude(self):
        coordinates = valid_gps_coordinates(self._vehicle)
        return coordinates[0] if coordinates else None

    @property
    def longitude(self):
        coordinates = valid_gps_coordinates(self._vehicle)
        return coordinates[1] if coordinates else None

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
