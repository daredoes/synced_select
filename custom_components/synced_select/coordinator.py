"""Coordinator for the Synced Select integration."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from collections.abc import Callable


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
                LOGGER.debug("Found %s with options: %s", entity_id, options)
                if isinstance(options, list):
                    for option in options:
                        all_shared_opts[option] += 1

        if not self._listeners_setup:
            self._unsubscribe = async_track_state_change_event(
                self.hass, self.source_entities, self._handle_state_change
            )
            self._listeners_setup = True
        shared = [
            option
            for option, count in all_shared_opts.items()
            if count == total_entities
        ]
        LOGGER.debug(
            "Computed %d shared option(s) across %d entities: %s",
            len(shared),
            total_entities,
            shared,
        )
        return shared

    async def async_unload(self) -> None:
        """Unload the coordinator and clean up listeners."""
        if self._unsubscribe:
            self._unsubscribe()

    @callback
    def _handle_state_change(self, event) -> None:
        """Handle source-entity state changes by requesting a (debounced) refresh."""
        self.hass.async_create_task(self.async_request_refresh())
