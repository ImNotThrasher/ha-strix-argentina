"""Asynchronous Strix API client with classified, secret-safe failures."""

import asyncio
import time

import aiohttp

BASE = "https://api.strix.com.ar"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)


class StrixApiError(Exception):
    """Strix returned an invalid response or HTTP error."""


class StrixAuthenticationError(StrixApiError):
    """Strix rejected credentials or authorization."""


class StrixConnectionError(StrixApiError):
    """Network or timeout failure contacting Strix."""


class StrixClient:
    """Fetch vehicles using OAuth access and refresh tokens."""

    def __init__(self, session, username, password, client_device_id, oauth_basic):
        self.session = session
        self.username = username
        self.password = password
        self.device_id = client_device_id
        self.oauth_basic = oauth_basic.strip()
        self.token = None
        self.refresh_token = None
        self.expires_at = 0
        self.lock = asyncio.Lock()

    def _auth_payload(self):
        """Prefer refresh credentials, falling back to account credentials."""
        if self.refresh_token:
            return {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_device_id": self.device_id,
            }
        return {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_device_id": self.device_id,
        }

    async def authenticate(self):
        """Refresh access token; retry with password if refresh is rejected."""
        async with self.lock:
            if self.token and time.monotonic() < self.expires_at:
                return

            payload = self._auth_payload()
            for attempt in range(2):
                try:
                    async with self.session.post(
                        BASE + "/oauth/token",
                        data=payload,
                        headers={"Authorization": "Basic " + self.oauth_basic},
                        timeout=REQUEST_TIMEOUT,
                    ) as response:
                        if response.status >= 400:
                            if attempt == 0 and self.refresh_token:
                                self.refresh_token = None
                                payload = self._auth_payload()
                                continue
                            if response.status in (400, 401, 403):
                                raise StrixAuthenticationError(
                                    "Strix authentication rejected (HTTP %s)" % response.status
                                )
                            raise StrixApiError("Strix auth HTTP %s" % response.status)
                        data = await response.json(content_type=None)
                except (aiohttp.ClientError, TimeoutError) as exc:
                    raise StrixConnectionError("Strix authentication unavailable") from exc
                except (ValueError, TypeError, KeyError) as exc:
                    raise StrixApiError("Invalid Strix authentication response") from exc

                if not isinstance(data, dict) or not isinstance(data.get("access_token"), str) or not data["access_token"]:
                    raise StrixApiError("Missing Strix access token")
                self.token = data["access_token"]
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                try:
                    lifetime = int(data.get("expires_in", 900))
                except (TypeError, ValueError) as exc:
                    raise StrixApiError("Invalid token expiry") from exc
                self.expires_at = time.monotonic() + max(30, lifetime - 60)
                return

    async def vehicles(self):
        """Return Strix vehicles keyed by their stable identifiers."""
        await self.authenticate()
        for attempt in range(2):
            try:
                async with self.session.get(
                    BASE + "/things",
                    headers={"Authorization": "Bearer " + self.token},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    if response.status == 401:
                        if attempt == 0:
                            self.token = None
                            await self.authenticate()
                            continue
                        raise StrixAuthenticationError("Strix authorization rejected")
                    if response.status >= 400:
                        raise StrixApiError("Strix API HTTP %s" % response.status)
                    data = await response.json(content_type=None)
            except (aiohttp.ClientError, TimeoutError) as exc:
                raise StrixConnectionError("Strix vehicles unavailable") from exc
            except (ValueError, TypeError) as exc:
                raise StrixApiError("Invalid Strix vehicles response") from exc

            if not isinstance(data, list):
                raise StrixApiError("Unexpected Strix vehicles response")
            if any(not isinstance(v, dict) for v in data):
                raise StrixApiError("Malformed Strix vehicle entry")
            return {
                vehicle["id"]: vehicle
                for vehicle in data
                if isinstance(vehicle, dict)
                and vehicle.get("type") == "mrn:things:vehicle"
                and vehicle.get("id")
            }
        raise StrixAuthenticationError("Strix authorization rejected")
