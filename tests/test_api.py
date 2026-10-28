"""Offline OAuth and vehicle API tests with synthetic credentials only."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "strix_argentina"
PACKAGE = "strix_argentina"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

spec = importlib.util.spec_from_file_location(PACKAGE + ".api", ROOT / "api.py")
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)


class Response:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, **kwargs):
        return self.payload


class Session:
    def __init__(self, post_responses, get_responses):
        self.post_responses = iter(post_responses)
        self.get_responses = iter(get_responses)
        self.posts = []
        self.gets = []

    def post(self, url, **kwargs):
        self.posts.append(kwargs)
        return next(self.post_responses)

    def get(self, url, **kwargs):
        self.gets.append(kwargs)
        return next(self.get_responses)


def client(session):
    return api.StrixClient(session, "demo", "example", "synthetic-device", "synthetic-basic")


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_password_auth_and_vehicle_filter(self):
        session = Session(
            [Response(200, {"access_token": "access", "refresh_token": "refresh"})],
            [Response(200, [{"id": "v1", "type": "mrn:things:vehicle"},
                            {"id": "x", "type": "other"}])],
        )
        result = await client(session).vehicles()
        self.assertEqual(list(result), ["v1"])
        self.assertEqual(session.posts[0]["data"]["grant_type"], "password")

    async def test_refresh_rejection_falls_back_to_password(self):
        session = Session(
            [Response(401, {}), Response(200, {"access_token": "new"})], []
        )
        obj = client(session)
        obj.refresh_token = "expired"
        await obj.authenticate()
        self.assertEqual([p["data"]["grant_type"] for p in session.posts],
                         ["refresh_token", "password"])

    async def test_unauthorized_get_refreshes_token(self):
        session = Session(
            [Response(200, {"access_token": "one"}),
             Response(200, {"access_token": "two"})],
            [Response(401, {}), Response(200, [])],
        )
        self.assertEqual(await client(session).vehicles(), {})
        self.assertEqual(len(session.gets), 2)

    async def test_bad_credentials(self):
        session = Session([Response(401, {})], [])
        with self.assertRaises(api.StrixAuthenticationError):
            await client(session).authenticate()

    async def test_invalid_payload(self):
        session = Session([Response(200, {"access_token": "ok"})],
                          [Response(200, {"unexpected": "object"})])
        with self.assertRaises(api.StrixApiError):
            await client(session).vehicles()

    async def test_malformed_vehicle_item(self):
        session = Session([Response(200, {"access_token": "ok"})],
                          [Response(200, [{"id": "v1", "type": "mrn:things:vehicle"}, None])])
        with self.assertRaises(api.StrixApiError):
            await client(session).vehicles()

    async def test_non_string_token(self):
        session = Session([Response(200, {"access_token": 123})], [])
        with self.assertRaises(api.StrixApiError):
            await client(session).authenticate()

    async def test_concurrent_auth_uses_single_request(self):
        import asyncio
        session = Session([Response(200, {"access_token": "ok"})], [])
        obj = client(session)
        await asyncio.gather(obj.authenticate(), obj.authenticate())
        self.assertEqual(len(session.posts), 1)

    async def test_network_failure(self):
        import aiohttp
        session = Session([Response(200, {"access_token": "ok"})], [])
        session.get = Mock(side_effect=aiohttp.ClientConnectionError("offline"))
        with self.assertRaises(api.StrixConnectionError):
            await client(session).vehicles()


if __name__ == "__main__":
    unittest.main()
