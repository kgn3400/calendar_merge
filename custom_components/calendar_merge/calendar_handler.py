"""Calendar handler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import partial
from typing import Any

from arrow.locales import get_locale
from babel.dates import format_date, format_time, format_timedelta, get_datetime_format

from homeassistant.components.calendar import CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

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
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
    TRANSLATION_KEY_MISSING_ENTITY,
    TRANSLATION_KEY_TEMPLATE_ERROR,
)


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class CalendarAttrEvent:
    """Calendar attr event."""

    def __init__(
        self,
        calender_merge_event: CalendarMergeEvent,
    ) -> None:
        """Init."""

        self.calendar: str = calender_merge_event.calendar
        self.start: datetime | date = calender_merge_event.start
        self.end: datetime | date = calender_merge_event.end
        self.summary: str = calender_merge_event.summary
        self.description: str | None = (
            calender_merge_event.description
            if calender_merge_event.description is not None
            else ""
        )
        self.location: str | None = (
            calender_merge_event.location
            if calender_merge_event.location is not None
            else ""
        )


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class CalendarMergeEvent(CalendarEvent):
    """Calendar merge event."""

    # ------------------------------------------------------
    def __init__(
        self,
        calendar: str,
        start: datetime | date | str,
        end: datetime | date | str,
        summary: str,
        description: str | None = None,
        location: str | None = None,
    ) -> None:
        """Init."""

        self.calendar: str = calendar

        if isinstance(start, str):
            if len(start) == 10:
                tmp_start: date = date.fromisoformat(start)
            else:
                tmp_start: datetime = datetime.fromisoformat(start)
        elif isinstance(start, date):
            tmp_start: date = start
        else:
            tmp_start: datetime = start

        if isinstance(end, str):
            if len(end) == 10:
                tmp_end: date = date.fromisoformat(end)
            else:
                tmp_end: datetime = datetime.fromisoformat(end)
        elif isinstance(end, date):
            tmp_end: date = end
        else:
            tmp_end: datetime = start

        if isinstance(tmp_start, datetime):
            super().__init__(
                dt_util.as_local(tmp_start),
                dt_util.as_local(tmp_end),
                summary,
                description,
                location,
            )
        else:
            super().__init__(
                tmp_start,
                tmp_end,
                summary,
                description,
                location,
            )

        self.formatted_start: str = ""
        self.formatted_end: str = ""
        self.formatted_event_time: str = ""
        self.formatted_event: str = ""
        super().__post_init__()

    # ------------------------------------------------------
    def as_calender_event(self) -> CalendarEvent:
        """As calendar event parms."""
        return CalendarEvent(
            self.start, self.end, self.summary, self.description, self.location
        )

    # ------------------------------------------------------
    def __eq__(self, other: CalendarMergeEvent) -> bool:
        """Eq."""
        return (
            self.calendar == other.calendar
            and self.start == other.start
            and self.end == other.end
            and self.summary == other.summary
            and self.description == other.description
            and self.location == other.location
            and self.all_day == other.all_day
        )


# ------------------------------------------------------
# ------------------------------------------------------
class CalendarHandler:
    """Calendar handler."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Init."""

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.events: list[CalendarMergeEvent] = []
        self.language: str = self.entry.options.get(
            CONF_FORMAT_LANGUAGE, self.hass.config.language
        )

        registry = er.async_get(hass)
        self.calendar_entities: list[str] = er.async_validate_entity_ids(
            registry, entry.options[CONF_CALENDAR_ENTITY_IDS]
        )

        self.last_error_template: str = ""
        self.last_error_txt_template: str = ""
        self.supress_update_listener: bool = False

        self.show_event_as_time_to: bool = entry.options.get(
            CONF_SHOW_EVENT_AS_TIME_TO, False
        )

    # ------------------------------------------------------
    async def merge_calendar_events(
        self,
    ) -> None:
        """Merge calendar events."""

        self.events = []

        try:
            tmp_events: dict = await self.hass.services.async_call(
                "calendar",
                "get_events",
                service_data={
                    ATTR_ENTITY_ID: self.calendar_entities,
                    "end_date_time": (
                        dt_util.now()
                        + timedelta(days=self.entry.options.get(CONF_DAYS_AHEAD, 30))
                    ).isoformat(),
                    "start_date_time": dt_util.now().isoformat(),
                },
                blocking=True,
                return_response=True,
            )
        # except (ServiceValidationError, ServiceNotFound, vol.Invalid) as err:
        except Exception as err:  # noqa: BLE001
            LOGGER.error(err)
            return

        for key in tmp_events:
            for event in tmp_events[key]["events"]:
                self.events.append(
                    CalendarMergeEvent(
                        str(key)
                        .replace("calendar.", "")
                        .replace("_", " ")
                        .capitalize(),
                        event["start"],
                        event["end"],
                        event.get("summary", ""),
                        event.get("description", ""),
                        event.get("location", ""),
                    )
                )

        if self.entry.options.get(CONF_REMOVE_RECURRING_EVENTS, True):
            self.remove_recurring_events()

        self.events.sort(key=lambda x: x.start_datetime_local.isoformat())
        self.events = self.events[: int(self.entry.options.get(CONF_MAX_EVENTS, 5))]

    # ------------------------------------------------------
    def remove_recurring_events(self) -> None:
        """Remove recurring events."""

        index: int = 0

        while index < (len(self.events) - 1):
            for index2, _ in reversed(list(enumerate(self.events))):
                if index2 <= index:
                    break
                if (
                    self.events[index].calendar == self.events[index2].calendar
                    and self.events[index].summary == self.events[index2].summary
                    and self.events[index].description
                    == self.events[index2].description
                    and self.events[index].start.time()
                    == self.events[index2].start.time()
                    and self.events[index].end.time() == self.events[index2].end.time()
                ):
                    del self.events[index2]
            index += 1

    # ------------------------------------------------------
    async def async_format_datetime(
        self,
        date_time: datetime | date,
    ) -> str | None:
        """Format datetime."""

        date_str: str = await self.hass.async_add_executor_job(
            partial(
                format_date,
                date=date_time,
                format="medium",
                locale=self.language,
            )
        )

        if isinstance(date_time, date):
            return date_str

        dt_format = await self.hass.async_add_executor_job(
            get_datetime_format, "medium", self.language
        )

        time_str: str = await self.hass.async_add_executor_job(
            partial(
                format_time,
                time=date_time,
                format="short",
                locale=self.language,
            )
        )

        return dt_format.format(time_str, date_str)

    # ------------------------------------------------------
    async def async_format_event(self, event_num: int) -> str | None:
        """Format event."""

        if event_num < len(self.events):
            tmp_event = self.events[event_num]

            tmp_event.formatted_start = await self.async_format_datetime(
                tmp_event.start
            )
            tmp_event.formatted_end = await self.async_format_datetime(tmp_event.end)

            diff: timedelta = tmp_event.start_datetime_local - dt_util.now()

            if tmp_event.all_day and diff.total_seconds() < 0:
                formatted_event_str: str = (
                    get_locale(self.language).timeframes.get("now", "now").capitalize()
                )

            elif self.show_event_as_time_to:
                formatted_event_str: str = await self.hass.async_add_executor_job(
                    partial(
                        format_timedelta,
                        delta=diff,
                        add_direction=True,
                        locale=self.language,
                    )
                )

            else:
                formatted_event_str = tmp_event.formatted_start
                if (
                    self.entry.options.get(CONF_SHOW_END_DATE, False)
                    and not tmp_event.all_day
                ):
                    formatted_event_str = (
                        formatted_event_str + " - " + tmp_event.formatted_end
                    )

            tmp_event.formatted_event_time = formatted_event_str

            if self.entry.options.get(CONF_SHOW_SUMMARY, False):
                formatted_event_str = tmp_event.summary + " : " + formatted_event_str

            tmp_event.formatted_event = formatted_event_str
            self.events[event_num] = tmp_event

            return formatted_event_str

        return None

    # ------------------------------------------------------------------
    def create_markdown(self) -> str:
        """Create markdown."""

        # ------------------------------------------------------------------
        def replace_markdown_tags(txt: str) -> str:
            """Replace markdown tags."""

            return txt.replace(".", "\\.").replace("-", "\\-").replace("+", "\\+")

        try:
            tmp_md: str = ""
            values: dict[str, Any] = {}

            if self.entry.options.get(CONF_MD_HEADER_TEMPLATE, "") != "":
                value_template: Template | None = Template(
                    str(self.entry.options.get(CONF_MD_HEADER_TEMPLATE, "")),
                    self.hass,
                )

                tmp_md = value_template.async_render({})

            for item in self.events:
                value_template: Template | None = Template(
                    str(self.entry.options.get(CONF_MD_ITEM_TEMPLATE, "")),
                    self.hass,
                )
                values = {
                    "calendar": replace_markdown_tags(item.calendar),
                    "start": replace_markdown_tags(item.start.isoformat()),
                    "end": replace_markdown_tags(item.end.isoformat()),
                    "all_day": item.all_day,
                    "summary": replace_markdown_tags(item.summary),
                    "description": replace_markdown_tags(item.description),
                    "location": replace_markdown_tags(item.location),
                    "formatted_start": replace_markdown_tags(item.formatted_start),
                    "formatted_end": replace_markdown_tags(item.formatted_end),
                    "formatted_event": replace_markdown_tags(item.formatted_event),
                    "formatted_event_time": replace_markdown_tags(
                        item.formatted_event_time
                    ),
                }
                tmp_md += value_template.async_render(values)

            tmp_md = tmp_md.replace("<br>", "\r")

        except (TypeError, TemplateError) as e:
            self.create_issue_template(
                str(e), value_template.template, TRANSLATION_KEY_TEMPLATE_ERROR
            )

        return tmp_md

    # ------------------------------------------------------------------
    def get_events_to_att(
        self,
    ) -> list[CalendarAttrEvent]:
        """Create list of events to attribute."""

        return [CalendarAttrEvent(event) for event in self.events]

    # ------------------------------------------------------------------
    def create_issue_template(
        self,
        error_txt: str,
        template: str,
        translation_key: str,
    ) -> None:
        """Create issue on entity."""

        if (
            self.last_error_template != template
            or error_txt != self.last_error_txt_template
        ):
            LOGGER.warning(error_txt)

            ir.async_create_issue(
                self.hass,
                DOMAIN,
                DOMAIN_NAME + datetime.now().isoformat(),
                issue_domain=DOMAIN,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=translation_key,
                translation_placeholders={
                    "template": template,
                    "calendar_events_helper": "sensor." + self.entry.title,
                    "error_txt": error_txt,
                },
            )
            self.last_error_template = template
            self.last_error_txt_template = error_txt

    # ------------------------------------------------------
    async def async_verify_calendar_entities_exist(self) -> bool:
        """Verify calendar entities exist."""
        res: bool = True

        for index, calendar_entity in reversed(list(enumerate(self.calendar_entities))):
            state: State | None = self.hass.states.get(calendar_entity)

            if state is None:
                self.create_issue(
                    calendar_entity,
                    TRANSLATION_KEY_MISSING_ENTITY,
                    {
                        "entity": calendar_entity,
                        "calendar_merge_helper": calendar_entity,
                    },
                )
                del self.calendar_entities[index]
                res = False

        return res
