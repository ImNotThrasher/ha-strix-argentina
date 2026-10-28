"""Shared Strix entity behavior; stable IDs are set by each platform."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import device_info


class StrixEntity(CoordinatorEntity):
    """Access the latest vehicle payload through the shared coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, vehicle_id):
        super().__init__(coordinator)
        self.vid = vehicle_id

    @property
    def vehicle(self):
        return self.coordinator.data.get(self.vid) or {}

    @property
    def device_info(self):
        return device_info(self.vehicle, self.vid)

    @property
    def available(self):
        return super().available and self.vid in self.coordinator.data
