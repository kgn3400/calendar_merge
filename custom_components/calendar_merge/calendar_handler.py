"""Calendar handler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import Any

from arrow.locales import get_locale
from babel.dates import format_date, format_time, format_timedelta, get_datetime_format

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

from .const import (
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
    TRANSLATION_KEY_TEMPLATE_ERROR,
)


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class CalendarMergeEvent:
    """Calendar merge event."""

    def __init__(
        self,
        calendar: str,
        start: str,
        end: str,
        summary: str,
        description: str,
        location: str,
    ) -> None:
        "Init."

        self.calendar: str = calendar
        self.start: str = start
        self.end: str = end
        self.all_day: bool = False
        self.summary: str = summary
        self.description: str = description
        self.location: str = location
        self.formatted_start: str = ""
        self.formatted_end: str = ""
        self.formatted_event_time: str = ""
        self.formatted_event: str = ""

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
        entry_options: dict[str, Any],
    ) -> None:
        """Init."""

        self.hass: HomeAssistant = hass
        self.entry: ConfigEntry = entry
        self.entry_options: dict[str, Any] = entry_options
        self.events: list[CalendarMergeEvent] = []
        self.language: str = self.entry_options.get(
            CONF_FORMAT_LANGUAGE, self.hass.config.language
        )

        self.last_error_template: str = ""
        self.last_error_txt_template: str = ""
        self.next_update: datetime = datetime.now()
        self.supress_update_listener: bool = False

    # ------------------------------------------------------
    async def get_merge_calendar_events(
        self,
        calendar_entities: list[str],
        force_update: bool = False,
    ) -> None:
        """Process calendar events."""

        if force_update or self.next_update < datetime.now():
            self.events = []

            try:
                tmp_events: dict = await self.hass.services.async_call(
                    "calendar",
                    "get_events",
                    service_data={
                        ATTR_ENTITY_ID: calendar_entities,
                        "end_date_time": (
                            dt_util.now()
                            + timedelta(
                                days=self.entry_options.get(CONF_DAYS_AHEAD, 30)
                            )
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

            if self.entry_options.get(CONF_REMOVE_RECURRING_EVENTS, True):
                self.remove_recurring_events()

            self.events.sort(key=lambda x: x.start)
            self.events = self.events[: int(self.entry_options.get(CONF_MAX_EVENTS, 5))]
            self.next_update = datetime.now() + timedelta(minutes=5)

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
                    and datetime.fromisoformat(self.events[index].start).time()
                    == datetime.fromisoformat(self.events[index2].start).time()
                    and datetime.fromisoformat(self.events[index].end).time()
                    == datetime.fromisoformat(self.events[index2].end).time()
                ):
                    del self.events[index2]
            index += 1

    # ------------------------------------------------------
    async def async_format_datetime(
        self,
        date_time: datetime,
        date_only: bool = False,
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

        if date_only:
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
            start_date: datetime = datetime.fromisoformat(tmp_event.start)
            start_date_next: datetime = start_date + timedelta(days=1)
            end_date: datetime = datetime.fromisoformat(tmp_event.end)

            if (
                start_date_next == end_date
                and start_date.hour == 0
                and start_date.minute == 0
                and end_date.hour == 0
                and end_date.minute == 0
            ):
                tmp_event.all_day = True
                tmp_event.formatted_start = await self.async_format_datetime(
                    start_date, date_only=True
                )
                tmp_event.formatted_end = await self.async_format_datetime(
                    end_date, date_only=True
                )
            else:
                tmp_event.formatted_start = await self.async_format_datetime(start_date)
                tmp_event.formatted_end = await self.async_format_datetime(end_date)

            diff: timedelta = start_date - datetime.now(start_date.tzinfo)

            if tmp_event.all_day and diff.total_seconds() < 0:
                formatted_event_str: str = (
                    get_locale(self.language).timeframes.get("now", "now").capitalize()
                )

            elif self.entry_options.get(CONF_SHOW_EVENT_AS_TIME_TO, False):
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
                    self.entry_options.get(CONF_SHOW_END_DATE, False)
                    and not tmp_event.all_day
                ):
                    formatted_event_str = (
                        formatted_event_str + " - " + tmp_event.formatted_end
                    )

            tmp_event.formatted_event_time = formatted_event_str

            if self.entry_options.get(CONF_SHOW_SUMMARY, False):
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

            if self.entry_options.get(CONF_MD_HEADER_TEMPLATE, "") != "":
                value_template: Template | None = Template(
                    str(self.entry_options.get(CONF_MD_HEADER_TEMPLATE, "")),
                    self.hass,
                )

                tmp_md = value_template.async_render({})

            for item in self.events:
                value_template: Template | None = Template(
                    str(self.entry_options.get(CONF_MD_ITEM_TEMPLATE, "")),
                    self.hass,
                )
                values = {
                    "calendar": replace_markdown_tags(item.calendar),
                    "start": replace_markdown_tags(item.start),
                    "end": replace_markdown_tags(item.end),
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
