"""Shared accessors for the Strix vehicle API payload.

Keep the payload parsing here so entities use the same defaults. These helpers
must not change entity unique IDs or the existing coordinate interpretation.
"""

from .const import DOMAIN


def vehicle_state(vehicle):
    """Return vehicle state, tolerating missing or null API fields."""
    return (vehicle or {}).get("state") or {}


def vehicle_info(vehicle):
    """Return descriptive metadata for a vehicle."""
    return (vehicle or {}).get("info") or {}


def gps_coordinates(vehicle):
    """Return coordinates in the order currently used by this integration.

    The Strix API coordinate convention still needs independent verification.
    Do not swap the values without checking real API responses.
    """
    location = vehicle_state(vehicle).get("location") or {}
    return location.get("coordinates") or []


def gps_timestamp_ms(vehicle):
    """Return the GPS timestamp in milliseconds, if present."""
    metadata = (vehicle or {}).get("metadata") or {}
    state = metadata.get("state") or {}
    return (state.get("location") or {}).get("timestamp")


def device_info(vehicle, vehicle_id, *, detailed=False):
    """Build shared device registry data without changing device identifiers."""
    info = vehicle_info(vehicle)
    data = {
        "identifiers": {(DOMAIN, vehicle_id)},
        "name": info.get("label") or "Strix vehicle",
    }
    if detailed:
        data.update(
            manufacturer=info.get("make") or "Strix",
            model=info.get("model") or "Vehicle",
            serial_number=vehicle_id,
        )
    return data
