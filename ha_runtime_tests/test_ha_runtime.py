"""Isolated Home Assistant runtime tests with synthetic vehicles only.

Run in GitHub Actions, never against a user's Home Assistant instance.
"""
from unittest.mock import Mock

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.strix_argentina import binary_sensor, device_tracker, sensor


@pytest.mark.asyncio
async def test_two_vehicles_create_independent_entities(hass):
    vehicles = {
        "test-vehicle-a": {
            "info": {"label": "Simulated car A"},
            "state": {"speed": 12, "location": {"coordinates": [-34.8, -58.4]}},
        },
        "test-vehicle-b": {
            "info": {"label": "Simulated car B"},
            "state": {"speed": 45, "location": {"coordinates": [-35.0, -58.6]}},
        },
    }
    entry = Mock()
    entry.entry_id = "isolated-test-entry"
    coordinator = DataUpdateCoordinator(hass, Mock(), name="Strix test", config_entry=entry)
    coordinator.async_set_updated_data(vehicles)
    coordinator.last_strix_success = lambda: None
    callbacks = []
    entry.async_on_unload.side_effect = callbacks.append
    hass.data.setdefault("strix_argentina", {})[entry.entry_id] = coordinator

    trackers, sensors, binaries = [], [], []
    await device_tracker.async_setup_entry(hass, entry, trackers.extend)
    await sensor.async_setup_entry(hass, entry, sensors.extend)
    await binary_sensor.async_setup_entry(hass, entry, binaries.extend)

    assert len(trackers) == 2
    assert len(sensors) == 2 * len(sensor.FIELDS)
    assert len(binaries) == 2 * len(binary_sensor.FIELDS)
    assert len({e.unique_id for e in trackers + sensors + binaries}) == (
        len(trackers) + len(sensors) + len(binaries)
    )
    assert {e.latitude for e in trackers} == {-34.8, -35.0}
    assert {e.native_value for e in sensors if e.field == "speed"} == {12, 45}
    assert {e.device_info["identifiers"].pop()[1] for e in trackers} == set(vehicles)

    coordinator.async_set_updated_data({
        **vehicles,
        "test-vehicle-c": {
            "info": {"label": "Simulated car C"},
            "state": {"speed": 5, "location": {"coordinates": [-34.9, -58.5]}},
        },
    })
    assert len(trackers) == 3
    assert len(sensors) == 3 * len(sensor.FIELDS)
    assert len(binaries) == 3 * len(binary_sensor.FIELDS)
    assert len({e.unique_id for e in trackers + sensors + binaries}) == (
        len(trackers) + len(sensors) + len(binaries)
    )

    coordinator.async_set_updated_data({"test-vehicle-b": vehicles["test-vehicle-b"]})
    assert not next(e for e in trackers if e.vid == "test-vehicle-a").available
    coordinator.async_set_updated_data(vehicles)
    assert len(trackers) == 3  # no duplicate on reappearance
    for callback in callbacks:
        callback()
