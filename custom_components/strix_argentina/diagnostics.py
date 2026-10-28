"""Safe integration diagnostics: no credentials, tokens, IDs or GPS coordinates."""

from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN

REDACT = {"username", "password", "oauth_basic", "client_device_id"}


async def async_get_config_entry_diagnostics(hass, entry):
    """Expose operational metadata without returning vehicle payloads."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "config": async_redact_data(dict(entry.data), REDACT),
        "last_update_success": coordinator.last_update_success,
        "vehicle_count": len(coordinator.data or {}),
        "poll_interval_seconds": coordinator.update_interval.total_seconds(),
    }
