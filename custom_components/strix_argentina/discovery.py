"""Register entities for newly discovered Strix vehicles."""

from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN


def discovery_signal(entry_id):
    """Return a per-config-entry dispatcher signal."""
    return f"{DOMAIN}_new_vehicles_{entry_id}"


def register_vehicle_discovery(hass, entry, coordinator, async_add_entities, factory):
    """Create existing entities and add new ones after coordinator refreshes."""
    known = set()

    def add_vehicles():
        new_ids = set(coordinator.data or {}) - known
        if new_ids:
            known.update(new_ids)
            async_add_entities(
                [entity for vehicle_id in sorted(new_ids) for entity in factory(vehicle_id)]
            )

    add_vehicles()

    # Dispatcher is emitted only when the coordinator discovers new vehicle IDs.
    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    entry.async_on_unload(
        async_dispatcher_connect(hass, discovery_signal(entry.entry_id), add_vehicles)
    )


def notify_new_vehicles(hass, entry_id):
    """Ask platforms to register entities after new vehicles appear."""
    async_dispatcher_send(hass, discovery_signal(entry_id))
