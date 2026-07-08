"""Tests for the Synced Select entity behavior."""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import DATA_INSTANCES
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.synced_select.const import CONF_ENTITIES, DOMAIN


async def _setup_entry(hass: HomeAssistant, entities: list[str]) -> str:
    """Set up a config entry over the given source entities, return the entity_id."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test",
        data={"name": "Test", CONF_ENTITIES: entities},
        options={CONF_ENTITIES: entities},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    [reg_entry] = er.async_entries_for_config_entry(registry, entry.entry_id)
    return reg_entry.entity_id


def _get_entity(hass: HomeAssistant, entity_id: str):
    """Fetch the live entity instance for the given select entity_id."""
    return hass.data[DATA_INSTANCES]["select"].get_entity(entity_id)


async def test_select_option_fans_out_to_sources(hass: HomeAssistant) -> None:
    """Selecting an option calls select_option on every source entity."""
    hass.states.async_set("select.a", "x", {"options": ["x", "y"]})
    hass.states.async_set("input_select.b", "x", {"options": ["x", "y"]})

    entity_id = await _setup_entry(hass, ["select.a", "input_select.b"])
    entity = _get_entity(hass, entity_id)

    # Register the mocks after setup so they override the real select_option service
    # that the select component registers while the platform is set up.
    select_calls = async_mock_service(hass, "select", "select_option")
    input_select_calls = async_mock_service(hass, "input_select", "select_option")

    await entity.async_select_option("x")
    await hass.async_block_till_done()

    assert [c.data["entity_id"] for c in select_calls] == ["select.a"]
    assert [c.data["entity_id"] for c in input_select_calls] == ["input_select.b"]
    assert all(c.data["option"] == "x" for c in select_calls + input_select_calls)


async def test_select_option_is_momentary(hass: HomeAssistant) -> None:
    """The control shows the picked option briefly, then resets to unset."""
    hass.states.async_set("input_select.b", "x", {"options": ["x", "y"]})

    entity_id = await _setup_entry(hass, ["input_select.b"])
    entity = _get_entity(hass, entity_id)
    async_mock_service(hass, "input_select", "select_option")

    await entity.async_select_option("x")
    assert entity.current_option == "x"

    # The reset runs on a 0.25s timer.
    await asyncio.sleep(0.3)
    await hass.async_block_till_done()
    assert entity.current_option is None
