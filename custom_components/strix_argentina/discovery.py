"""Register entities when the Strix coordinator discovers new vehicles."""


def register_vehicle_discovery(hass, entry, coordinator, async_add_entities, factory):
    """Add initial and future vehicle entities without changing unique IDs."""
    known = set()

    def add_vehicles():
        new_ids = set(coordinator.data or {}) - known
        if not new_ids:
            return
        known.update(new_ids)
        async_add_entities(
            [entity for vehicle_id in sorted(new_ids) for entity in factory(vehicle_id)]
        )

    add_vehicles()
    # HA notifies listeners after replacing coordinator.data on each refresh.
    entry.async_on_unload(coordinator.async_add_listener(add_vehicles))
