"""Set up Strix Argentina and share its vehicle update coordinator."""

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    StrixApiError,
    StrixAuthenticationError,
    StrixClient,
    StrixConnectionError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["device_tracker", "sensor", "binary_sensor"]


async def async_setup_entry(hass, entry):
    """Set up an account, retaining all existing device and entity IDs."""
    client = StrixClient(
        async_get_clientsession(hass),
        entry.data["username"],
        entry.data["password"],
        entry.data["client_device_id"],
        entry.data["oauth_basic"],
    )

    last_successful_poll = None

    async def update():
        """Fetch vehicles, reporting authentication failures separately."""
        nonlocal last_successful_poll
        try:
            vehicles = await client.vehicles()
            last_successful_poll = datetime.now(timezone.utc)
            return vehicles
        except StrixAuthenticationError as exc:
            raise ConfigEntryAuthFailed("Strix authentication rejected") from exc
        except (StrixConnectionError, StrixApiError) as exc:
            raise UpdateFailed(type(exc).__name__) from exc
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
    coordinator.last_strix_success = lambda: last_successful_poll
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload platforms and remove their shared coordinator."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
