import asyncio
import time
import aiohttp

BASE = "https://api.strix.com.ar"

class StrixClient:
    def __init__(self, session, username, password, client_device_id, oauth_basic):
        self.session, self.username, self.password, self.device_id = session, username, password, client_device_id
        self.token = self.refresh_token = None
        self.expires_at = 0
        self.lock = asyncio.Lock()
        self.oauth_basic = oauth_basic.strip()

    async def authenticate(self):
        async with self.lock:
            if self.token and time.monotonic() < self.expires_at:
                return
            payload = {"grant_type": "refresh_token", "refresh_token": self.refresh_token, "client_device_id": self.device_id} if self.refresh_token else {"grant_type": "password", "username": self.username, "password": self.password, "client_device_id": self.device_id}
            for attempt in range(2):
                async with self.session.post(BASE + "/oauth/token", data=payload, headers={"Authorization": "Basic " + self.oauth_basic}, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status >= 400:
                        if attempt == 0 and self.refresh_token:
                            self.refresh_token = None
                            payload = {"grant_type": "password", "username": self.username, "password": self.password, "client_device_id": self.device_id}
                            continue
                        raise RuntimeError("Strix authentication failed (HTTP %s)" % response.status)
                    data = await response.json(content_type=None)
                    self.token = data["access_token"]
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
                    self.expires_at = time.monotonic() + max(30, int(data.get("expires_in", 900)) - 60)
                    return

    async def vehicles(self):
        await self.authenticate()
        for attempt in range(2):
            async with self.session.get(BASE + "/things", headers={"Authorization": "Bearer " + self.token}, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status == 401 and attempt == 0:
                    self.token = None
                    await self.authenticate()
                    continue
                response.raise_for_status()
                data = await response.json(content_type=None)
                if not isinstance(data, list):
                    raise RuntimeError("Unexpected Strix response")
                return {v["id"]: v for v in data if v.get("type") == "mrn:things:vehicle" and v.get("id")}
        raise RuntimeError("Strix authorization failed")
