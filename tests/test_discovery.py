"""Test dynamic vehicle discovery without a Home Assistant runtime."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "strix_argentina"
PACKAGE = "strix_argentina"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

spec = importlib.util.spec_from_file_location(PACKAGE + ".discovery", ROOT / "discovery.py")
discovery = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = discovery
spec.loader.exec_module(discovery)


class Coordinator:
    def __init__(self):
        self.data = {"vehicle-a": {}}
        self.listeners = []

    def async_add_listener(self, callback):
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

    def refresh(self, data):
        self.data = data
        for callback in list(self.listeners):
            callback()


class Entry:
    def __init__(self):
        self.cleanup = []

    def async_on_unload(self, callback):
        self.cleanup.append(callback)


class DiscoveryTests(unittest.TestCase):
    def test_second_vehicle_entity_lifecycle(self):
        coordinator = Coordinator()
        entry = Entry()
        added = []
        fields = ("location", "speed", "contact_on", "gps_stale", "api_connected")
        discovery.register_vehicle_discovery(
            None, entry, coordinator, added.extend,
            lambda vid: [(vid, field) for field in fields],
        )
        self.assertEqual(len(added), len(fields))
        self.assertTrue(all(vid == "vehicle-a" for vid, _ in added))
        coordinator.refresh({"vehicle-a": {}, "vehicle-b": {}})
        self.assertEqual(len(added), 2 * len(fields))
        self.assertEqual(
            {(vid, field) for vid, field in added if vid == "vehicle-b"},
            {("vehicle-b", field) for field in fields},
        )
        coordinator.refresh({"vehicle-b": {}})
        self.assertEqual(len(added), 2 * len(fields))
        coordinator.refresh({"vehicle-a": {}, "vehicle-b": {}})
        self.assertEqual(len(added), 2 * len(fields))
        entry.cleanup[0]()
        coordinator.refresh({"vehicle-a": {}, "vehicle-b": {}, "vehicle-c": {}})
        self.assertEqual(len(added), 2 * len(fields))

    def test_adds_new_vehicles_only_once(self):
        coordinator = Coordinator()
        entry = Entry()
        added = []
        discovery.register_vehicle_discovery(
            None, entry, coordinator, added.extend, lambda vid: [vid + "_location"]
        )
        self.assertEqual(added, ["vehicle-a_location"])
        coordinator.refresh({"vehicle-a": {}, "vehicle-b": {}})
        self.assertEqual(added, ["vehicle-a_location", "vehicle-b_location"])
        coordinator.refresh({"vehicle-a": {}, "vehicle-b": {}})
        self.assertEqual(len(added), 2)
        entry.cleanup[0]()
        self.assertEqual(coordinator.listeners, [])


if __name__ == "__main__":
    unittest.main()
