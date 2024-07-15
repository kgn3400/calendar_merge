"""Config flow for Calendar merge helper."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    LanguageSelector,
    LanguageSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CALENDAR_ENTITY_IDS,
    CONF_DAYS_AHEAD,
    CONF_FORMAT_LANGUAGE,
    CONF_MAX_EVENTS,
    CONF_MD_HEADER_TEMPLATE,
    CONF_MD_ITEM_TEMPLATE,
    CONF_REMOVE_RECURRING_EVENTS,
    CONF_SHOW_END_DATE,
    CONF_SHOW_EVENT_AS_TIME_TO,
    CONF_SHOW_SUMMARY,
    CONF_USE_SUMMARY_AS_ENTITY_NAME,
    DOMAIN,
)

# ------------------------------------------------------------------
default_md_header_template = "### <font color= dodgerblue> <ha-icon icon='mdi:calendar-blank-outline'></ha-icon></font>  Kalenderbegivenheder <br>"
default_md_item_template = "- <font color= dodgerblue> <ha-icon icon='mdi:calendar-clock-outline'></ha-icon></font> __{{ summary }}__ <br>_{{ formatted_event_time }}_<br>"


async def _validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate user input."""
    if CONF_CALENDAR_ENTITY_IDS not in user_input:
        raise SchemaFlowError("missing_selection")

    if len(user_input[CONF_CALENDAR_ENTITY_IDS]) == 0:
        raise SchemaFlowError("missing_selection")

    return user_input


CONFIG_NAME = {
    vol.Required(
        CONF_NAME,
    ): selector.TextSelector(),
}

CONFIG_OPTIONS = {
    vol.Required(
        CONF_DAYS_AHEAD,
        default=15,
    ): NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=999,
            step="any",
            mode=NumberSelectorMode.BOX,
        )
    ),
    vol.Required(
        CONF_MAX_EVENTS,
        default=5,
    ): NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=20,
            step="any",
            mode=NumberSelectorMode.BOX,
        )
    ),
    vol.Required(
        CONF_REMOVE_RECURRING_EVENTS,
        default=True,
    ): BooleanSelector(),
}

CONFIG_OPTIONS_ENTITIES = {
    vol.Required(
        CONF_CALENDAR_ENTITY_IDS,
        default=[],
    ): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="calendar", multiple=True),
    ),
}


# ------------------------------------------------------------------
async def format_schema(handler: SchemaCommonFlowHandler) -> vol.Schema:
    """Return schema for the format step."""

    return vol.Schema(
        {
            vol.Required(
                CONF_SHOW_EVENT_AS_TIME_TO,
                default=False,
            ): BooleanSelector(),
            vol.Required(
                CONF_SHOW_END_DATE,
                default=False,
            ): BooleanSelector(),
            vol.Required(
                CONF_SHOW_SUMMARY,
                default=True,
            ): BooleanSelector(),
            vol.Required(
                CONF_USE_SUMMARY_AS_ENTITY_NAME,
                default=False,
            ): BooleanSelector(),
            vol.Required(
                CONF_FORMAT_LANGUAGE,
                default=handler.parent_handler.hass.config.language,
            ): LanguageSelector(LanguageSelectorConfig()),
            vol.Optional(
                CONF_MD_HEADER_TEMPLATE,
                default=default_md_header_template,
            ): TextSelector(
                TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_MD_ITEM_TEMPLATE,
                default=default_md_item_template,
            ): TextSelector(
                TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
            ),
        }
    )


CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(
        vol.Schema(
            {
                **CONFIG_NAME,
                **CONFIG_OPTIONS,
                **CONFIG_OPTIONS_ENTITIES,
            }
        ),
        next_step="user_format",
        validate_user_input=_validate_input,
    ),
    "user_format": SchemaFlowFormStep(format_schema),
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(
        vol.Schema(
            {
                **CONFIG_OPTIONS,
                **CONFIG_OPTIONS_ENTITIES,
            }
        ),
        next_step="init_format",
        validate_user_input=_validate_input,
    ),
    "init_format": SchemaFlowFormStep(format_schema),
}


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    # ------------------------------------------------------------------
    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, options[CONF_NAME])

    # ------------------------------------------------------------------
    @callback
    def async_config_flow_finished(self, options: Mapping[str, Any]) -> None:
        """Take necessary actions after the config flow is finished, if needed.

        The options parameter contains config entry options, which is the union of user
        input from the config flow steps.
        """
