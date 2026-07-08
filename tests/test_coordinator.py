"""Tests for the Synced Select coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.synced_select.coordinator import SyncedSelectCoordinator


async def test_options_are_the_common_intersection(hass: HomeAssistant) -> None:
    """Only options present on every source entity are published."""
    hass.states.async_set("select.a", "x", {"options": ["x", "y", "z"]})
    hass.states.async_set("select.b", "x", {"options": ["x", "y"]})

    coordinator = SyncedSelectCoordinator(hass, "entry", ["select.a", "select.b"])
    await coordinator.async_refresh()

    assert set(coordinator.data) == {"x", "y"}


async def test_missing_source_state_yields_no_common_options(
    hass: HomeAssistant,
) -> None:
    """An unavailable source (no state) means nothing is shared with it."""
    hass.states.async_set("select.a", "x", {"options": ["x", "y"]})

    coordinator = SyncedSelectCoordinator(hass, "entry", ["select.a", "select.b"])
    await coordinator.async_refresh()

    assert coordinator.data == []


async def test_recompute_when_source_options_change(hass: HomeAssistant) -> None:
    """Recomputing after a source narrows its options shrinks the shared set."""
    hass.states.async_set("select.a", "x", {"options": ["x", "y"]})
    hass.states.async_set("select.b", "x", {"options": ["x", "y"]})

    coordinator = SyncedSelectCoordinator(hass, "entry", ["select.a", "select.b"])
    await coordinator.async_refresh()
    assert set(coordinator.data) == {"x", "y"}

    hass.states.async_set("select.b", "x", {"options": ["x"]})
    await coordinator.async_refresh()
    assert coordinator.data == ["x"]


async def test_unload_removes_state_listener(hass: HomeAssistant) -> None:
    """After unload, source state changes no longer trigger a refresh (Bug 1)."""
    hass.states.async_set("select.a", "x", {"options": ["x"]})

    coordinator = SyncedSelectCoordinator(hass, "entry", ["select.a"])
    await coordinator.async_refresh()  # first refresh wires up the listener

    coordinator.async_request_refresh = AsyncMock()

    # While subscribed, a source change schedules a refresh.
    hass.states.async_set("select.a", "x", {"options": ["x", "y"]})
    await hass.async_block_till_done()
    assert coordinator.async_request_refresh.called

    coordinator.async_request_refresh.reset_mock()

    # After unload, the same change must not schedule anything.
    await coordinator.async_unload()
    hass.states.async_set("select.a", "x", {"options": ["x", "y", "z"]})
    await hass.async_block_till_done()
    assert not coordinator.async_request_refresh.called
