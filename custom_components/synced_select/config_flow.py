"""Config flow for Synced Select integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, selector

from .const import DOMAIN, CONF_ENTITIES, LOGGER


def get_select_entities(hass: HomeAssistant) -> list[str]:
    """Get all select and input_select entities."""
    return (
        hass.states.async_entity_ids("select")
        + hass.states.async_entity_ids("input_select")
    )



class SyncedSelectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Synced Select."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "SyncedSelectOptionsFlowHandler":
        """Get the options flow for this handler."""
        return SyncedSelectOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required(CONF_ENTITIES): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["select", "input_select"], multiple=True),
                    ),
                }
            ),
        )

class SyncedSelectOptionsFlowHandler(OptionsFlow):
    """Handle an options flow for Synced Select."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry_id = config_entry.entry_id

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)

        entity_registry = er.async_get(self.hass)
        entities_to_exclude = [ 
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.config_entry_id == config_entry.entry_id
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENTITIES,
                        default=config_entry.options.get(CONF_ENTITIES, []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["select", "input_select"], 
                            multiple=True,
                            exclude_entities=entities_to_exclude
                        ),
                    ),
                }
            ),
        )
