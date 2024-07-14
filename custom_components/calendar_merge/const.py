"""Constants for Calendar merge integration."""

from logging import Logger, getLogger

DOMAIN = "calendar_merge"
DOMAIN_NAME = "Calendar Merge"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
TRANSLATION_KEY_MISSING_ENTITY = "missing_entity"
TRANSLATION_KEY_MISSING__TIMER_ENTITY = "missing_timer_entity"
TRANSLATION_KEY_TEMPLATE_ERROR = "template_error"

CONF_DAYS_AHEAD = "days_ahead"
CONF_MAX_EVENTS = "max_events"
CONF_CALENDAR_ENTITY_IDS = "calender_entity_ids"
CONF_REMOVE_RECURRING_EVENTS = "remove_recurring_events"
CONF_SHOW_EVENT_AS_TIME_TO = "show_event_as_time_to"
CONF_SHOW_END_DATE = "show_show_end_date"
CONF_SHOW_SUMMARY = "show_summary"
CONF_USE_SUMMARY_AS_ENTITY_NAME = "use_summary_as_entity_name"
CONF_FORMAT_LANGUAGE = "format_language"

CONF_MD_HEADER_TEMPLATE = "md_header_template"
CONF_DEFAULT_MD_HEADER_TEMPLATE = "defaults.default_md_header_template"

CONF_MD_ITEM_TEMPLATE = "md_item_template"
CONF_DEFAULT_MD_ITEM_TEMPLATE = "defaults.default_md_item_template"

SERVICE_SAVE_SETTINGS = "save_settings"
