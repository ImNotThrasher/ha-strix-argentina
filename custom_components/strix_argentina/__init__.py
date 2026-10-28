"""Set up the Strix Argentina integration and shared update coordinator."""

from datetime import timedelta
import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StrixClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["device_tracker", "sensor", "binary_sensor"]


async def async_setup_entry(hass, entry):
    """Set up one account and share its polled data with all platforms."""
    client = StrixClient(
        async_get_clientsession(hass),
        entry.data["username"],
        entry.data["password"],
        entry.data["client_device_id"],
        entry.data["oauth_basic"],
    )

    async def update():
        """Retrieve vehicle data without exposing sensitive error details."""
        try:
            return await client.vehicles()
        except Exception as exc:
            raise UpdateFailed(
                "Strix update failed: " + type(exc).__name__
            ) from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Strix Argentina",
        update_method=update,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload all platforms and clean up the coordinator."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
