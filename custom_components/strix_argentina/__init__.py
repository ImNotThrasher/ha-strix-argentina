from datetime import timedelta
import logging
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import StrixClient
from .const import DOMAIN

PLATFORMS = ["device_tracker", "sensor", "binary_sensor"]

async def async_setup_entry(hass, entry):
    client = StrixClient(async_get_clientsession(hass), entry.data["username"], entry.data["password"], entry.data["client_device_id"], entry.data["oauth_basic"])
    async def update():
        try:
            return await client.vehicles()
        except Exception as exc:
            raise UpdateFailed("Strix update failed: " + type(exc).__name__) from exc
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="Strix Argentina", update_method=update, update_interval=timedelta(minutes=2))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
