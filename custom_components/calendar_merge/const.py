"""Constants for Calendar merge integration."""

from logging import Logger, getLogger

DOMAIN = "calendar_merge"
DOMAIN_NAME = "Calendar Merge"
LOGGER: Logger = getLogger(__name__)

TRANSLATION_KEY = DOMAIN
TRANSLATION_KEY_MISSING_CALENDER = "missing_calendar"
TRANSLATION_KEY_TEMPLATE_ERROR = "template_error"
TRANSLATION_KEY_FORMAT_DATE = "format_date"
TRANSLATION_KEY_SWITCH_SHOW_AS_TIME_TO = "switch_show_as_time_to"
CONF_DAYS_AHEAD = "days_ahead"
CONF_MAX_EVENTS = "max_events"
CONF_CALENDAR_ENTITY_IDS = "calender_entity_ids"
CONF_REMOVE_RECURRING_EVENTS = "remove_recurring_events"
CONF_FORMAT_DATE = "format_date"
CONF_FORMAT_DATE_FULL = "full"
CONF_FORMAT_DATE_LONG = "long"
CONF_FORMAT_DATE_MEDIUM = "medium"
CONF_FORMAT_DATE_SHORT = "short"
CONF_SHOW_EVENT_AS_TIME_TO = "show_event_as_time_to"
CONF_USE_SUMMARY_AS_ENTITY_NAME = "use_summary_as_entity_name"

CONF_MD_HEADER_TEMPLATE = "md_header_template"
CONF_DEFAULT_MD_HEADER_TEMPLATE = "defaults.default_md_header_template"

CONF_MD_ITEM_TEMPLATE = "md_item_template"
CONF_DEFAULT_MD_ITEM_TEMPLATE = "defaults.default_md_item_template"

CONF_EVENT_TEMPLATE = "event_template"
CONF_EVENT_TEMPLATE_DEFAULT = "{{ formatted_event_time }} - {{ summary }}"

SERVICE_SAVE_SETTINGS = "save_settings"
