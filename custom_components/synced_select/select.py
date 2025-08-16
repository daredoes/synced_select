"""Select platform for the Synced Select integration."""

from __future__ import annotations

import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ENTITIES
from .coordinator import SyncedSelectCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Synced Select select entity."""
    entities = entry.options.get(CONF_ENTITIES, entry.data.get(CONF_ENTITIES, []))
    coordinator = SyncedSelectCoordinator(hass, entry.entry_id, entities)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async_add_entities([SyncedSelectEntity(coordinator, entry)])


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the Synced Select select entity."""
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_unload()
    return True


class SyncedSelectEntity(CoordinatorEntity[SyncedSelectCoordinator], SelectEntity):
    """A select entity that synchronizes with other select entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SyncedSelectCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the synced select entity."""
        super().__init__(coordinator)
        self._attr_name = "Synced Select"
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["name"],
        )
        self._attr_options = coordinator.data or []
        self._attr_current_option = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_options = self.coordinator.data or []
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Select an option and propagate it to source entities."""
        self._attr_current_option = option
        self.async_write_ha_state()

        for entity_id in self.coordinator.source_entities:
            domain, _ = entity_id.split(".")
            await self.hass.services.async_call(
                domain,
                "select_option",
                {"entity_id": entity_id, "option": option},
                blocking=False,
            )

        self.hass.async_create_task(self._reset_state())

    async def _reset_state(self) -> None:
        """Reset the select entity state after a delay."""
        await asyncio.sleep(0.25)
        self._attr_current_option = None
        self.async_write_ha_state()
