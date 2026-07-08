"""Tests for the Synced Select config and options flows."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.synced_select.const import CONF_ENTITIES, DOMAIN


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """The user step creates an entry from a name and a set of entities."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Fan modes", CONF_ENTITIES: ["input_select.mode"]},
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Fan modes"
    assert result["data"][CONF_ENTITIES] == ["input_select.mode"]


async def test_options_flow_updates_entities(hass: HomeAssistant) -> None:
    """The options step updates the synced entity set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Fan modes",
        data={"name": "Fan modes", CONF_ENTITIES: ["input_select.a"]},
        options={CONF_ENTITIES: ["input_select.a"]},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_ENTITIES: ["input_select.a", "input_select.b"]},
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ENTITIES] == ["input_select.a", "input_select.b"]
