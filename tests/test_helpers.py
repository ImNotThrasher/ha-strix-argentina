"""Regression tests for pure Strix payload helpers.

Run with: python -m unittest discover -s tests
"""

import importlib.util
from pathlib import Path
import sys
import types
import unittest

# Load helpers without requiring a full Home Assistant installation.
PACKAGE = "strix_argentina"
ROOT = Path(__file__).resolve().parents[1] / "custom_components" / PACKAGE
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules.setdefault(PACKAGE, package)


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.{name}", ROOT / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load_module("const")
helpers = load_module("helpers")


class VehicleHelpersTests(unittest.TestCase):
    """Verify parsing defaults and stable device registry identifiers."""

    def test_missing_fields(self):
        self.assertEqual(helpers.vehicle_state({}), {})
        self.assertEqual(helpers.vehicle_info({}), {})
        self.assertEqual(helpers.gps_coordinates({}), [])
        self.assertIsNone(helpers.gps_timestamp_ms({}))

    def test_location_fields(self):
        vehicle = {
            "state": {"location": {"coordinates": [-34.8, -58.4]}},
            "metadata": {"state": {"location": {"timestamp": 1234567890000}}},
        }
        self.assertEqual(helpers.gps_coordinates(vehicle), [-34.8, -58.4])
        self.assertEqual(helpers.gps_timestamp_ms(vehicle), 1234567890000)

    def test_invalid_coordinates(self):
        for coordinates in ([], [91, 0], [0, 181], ["nan", 2], ["bad", 2]):
            self.assertIsNone(helpers.valid_gps_coordinates(
                {"state": {"location": {"coordinates": coordinates}}}
            ))
        self.assertEqual(helpers.valid_gps_coordinates(
            {"state": {"location": {"coordinates": [-34.8, -58.4]}}}
        ), (-34.8, -58.4))

    def test_device_info_keeps_identifiers(self):
        vehicle = {"info": {"label": "My car", "make": "Chevrolet"}}
        self.assertEqual(
            helpers.device_info(vehicle, "vehicle-123")["identifiers"],
            {("strix_argentina", "vehicle-123")},
        )
        self.assertEqual(
            helpers.device_info(vehicle, "vehicle-123", detailed=True)[
                "manufacturer"
            ],
            "Chevrolet",
        )


if __name__ == "__main__":
    unittest.main()
