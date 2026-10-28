"""Minimal asynchronous client for the unofficial Strix Argentina API."""

import asyncio
import time

import aiohttp

BASE = "https://api.strix.com.ar"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)


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
        """Prefer refresh credentials; fall back to account credentials."""
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
        """Refresh the access token, retrying with a password if needed."""
        async with self.lock:
            if self.token and time.monotonic() < self.expires_at:
                return

            payload = self._auth_payload()
            for attempt in range(2):
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
                        raise RuntimeError(
                            "Strix authentication failed (HTTP %s)" % response.status
                        )

                    data = await response.json(content_type=None)
                    self.token = data["access_token"]
                    self.refresh_token = data.get(
                        "refresh_token", self.refresh_token
                    )
                    self.expires_at = time.monotonic() + max(
                        30, int(data.get("expires_in", 900)) - 60
                    )
                    return

    async def vehicles(self):
        """Return API vehicles keyed by stable Strix vehicle ID."""
        await self.authenticate()

        for attempt in range(2):
            async with self.session.get(
                BASE + "/things",
                headers={"Authorization": "Bearer " + self.token},
                timeout=REQUEST_TIMEOUT,
            ) as response:
                if response.status == 401 and attempt == 0:
                    self.token = None
                    await self.authenticate()
                    continue

                response.raise_for_status()
                data = await response.json(content_type=None)
                if not isinstance(data, list):
                    raise RuntimeError("Unexpected Strix response")

                return {
                    vehicle["id"]: vehicle
                    for vehicle in data
                    if vehicle.get("type") == "mrn:things:vehicle"
                    and vehicle.get("id")
                }

        raise RuntimeError("Strix authorization failed")
