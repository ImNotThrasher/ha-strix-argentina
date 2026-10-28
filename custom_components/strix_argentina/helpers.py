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


def valid_gps_coordinates(vehicle):
    """Validate latitude and longitude while preserving existing ordering."""
    import math

    coordinates = gps_coordinates(vehicle)
    if not isinstance(coordinates, (list, tuple)) or len(coordinates) < 2:
        return None
    try:
        lat, lon = float(coordinates[0]), float(coordinates[1])
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(lat) or not math.isfinite(lon):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon
