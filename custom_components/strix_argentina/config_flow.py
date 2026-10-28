"""Configuration flow for Strix Argentina accounts."""

import logging
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import StrixClient, StrixAuthenticationError, StrixConnectionError, StrixApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Mask credentials in the UI. Keep storage keys unchanged for existing entries.
_SECRET = selector.TextSelector(
    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
)
SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): _SECRET,
        vol.Optional("client_device_id", default=""): str,
        vol.Required("oauth_basic"): _SECRET,
    }
)


class StrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Authenticate a Strix account before creating its config entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Validate credentials and configure the integration."""
        errors = {}
        if user_input is not None:
            user_input["client_device_id"] = (
                user_input.get("client_device_id") or str(uuid.uuid4())
            )
            user_input["oauth_basic"] = (
                user_input["oauth_basic"].strip().removeprefix("Basic ").strip()
            )
            try:
                client = StrixClient(async_get_clientsession(self.hass), **user_input)
                await client.vehicles()
            except Exception as exc:
                # Do not log credentials, tokens, response bodies or URLs.
                status = getattr(exc, "status", "unknown")
                _LOGGER.warning(
                    "Strix setup failed: error_type=%s status=%s",
                    type(exc).__name__,
                    status,
                )
                errors["base"] = "invalid_auth" if isinstance(exc, StrixAuthenticationError) else "cannot_connect"
            else:
                await self.async_set_unique_id(user_input["username"].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Strix Argentina", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=SCHEMA, errors=errors
        )

    async def async_step_reauth(self, entry_data):
        """Start reauthentication for an existing account."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Validate a new password without changing existing entity IDs."""
        errors = {}
        if user_input is not None:
            data = {**self._reauth_entry.data, **user_input}
            try:
                await StrixClient(async_get_clientsession(self.hass), **data).vehicles()
            except StrixAuthenticationError:
                errors["base"] = "invalid_auth"
            except (StrixConnectionError, StrixApiError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected Strix reauthentication error")
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry, data_updates=data
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required("password"): _SECRET}),
            errors=errors,
        )
