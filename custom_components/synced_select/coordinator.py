"""Coordinator for the Synced Select integration."""

from __future__ import annotations
from collections import defaultdict

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.event import async_track_state_change_event

from .const import LOGGER, DOMAIN, CONF_ENTITIES


class SyncedSelectCoordinator(DataUpdateCoordinator[list[str]]):
    """Coordinator for Synced Select entities."""

    def __init__(self, hass: HomeAssistant, entry_id: str, entities: list[str]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}-{entry_id}",
        )
        self.source_entities = entities
        self._listeners_setup = False
        self._unsubscribe: Callable[[], None] | None = None

    async def _async_update_data(self) -> list[str]:
        """Fetch the common options from the source entities."""
        all_shared_opts: dict[str, int] = defaultdict(lambda: 0)
        total_entities = len(self.source_entities)
        for entity_id in self.source_entities:
            state = self.hass.states.get(entity_id)
            if state:
                options = state.attributes.get("options")
                LOGGER.info(f"Found {entity_id} with options: {options} {isinstance(options, list)}")
                if isinstance(options, list):
                    for option in options:
                        all_shared_opts[option] += 1

        if not self._listeners_setup:
            self._unsubscribe = async_track_state_change_event(
                self.hass, self.source_entities, self._handle_state_change
            )
            self._listeners_setup = True
        LOGGER.info(f"Found {total_entities} entities with options: {all_shared_opts.keys()}")
        return [option for option, count in all_shared_opts.items() if count == total_entities]

    async def async_unload(self) -> None:
        """Unload the coordinator and clean up listeners."""
        if self._unsubscribe:
            self._unsubscribe()

    @callback
    def _handle_state_change(self, event) -> None:
        """Handle state changes for source entities and request a refresh."""
        self.hass.async_create_task(self.async_request_refresh())
