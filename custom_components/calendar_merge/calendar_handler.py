"""Calendar handler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from arrow.locales import get_locale
from babel.dates import (
    format_date as babel_format_date,
    format_time as babel_format_time,
    format_timedelta as babel_format_timedelta,
    get_datetime_format as babel_get_datetime_format,
)

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
    CONF_CALENDAR_PREFIX_IN_SUMMARY,
    CONF_DAYS_AHEAD,
    CONF_EVENT_TEMPLATE,
    CONF_EVENT_TEMPLATE_DEFAULT,
    CONF_FORMAT_DATE,
    CONF_MAX_EVENTS,
    CONF_MD_HEADER_TEMPLATE,
    CONF_MD_ITEM_TEMPLATE,
    CONF_REMOVE_RECURRING_EVENTS,
    CONF_SHOW_EVENT_AS_TIME_TO,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
    TRANSLATION_KEY_MISSING_CALENDER,
    TRANSLATION_KEY_TEMPLATE_ERROR,
)
from .hass_util import async_get_user_language, async_hass_add_executor_job


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
        self.formatted_start_date: str = ""
        self.formatted_start_time: str = ""
        self.formatted_end: str = ""
        self.formatted_end_date: str = ""
        self.formatted_end_time: str = ""
        self.formatted_time_to: str = ""
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

        self.entity_id: str = ""
        registry = er.async_get(hass)
        self.calendar_entities: list[str] = er.async_validate_entity_ids(
            registry, entry.options[CONF_CALENDAR_ENTITY_IDS]
        )

        self.last_error_template: str = ""
        self.last_error_txt_template: str = ""
        self.show_event_as_time_to: bool = entry.options.get(
            CONF_SHOW_EVENT_AS_TIME_TO, False
        )

    # ------------------------------------------------------
    async def async_init(
        self,
    ) -> None:
        """Async init."""
        self.language = await async_get_user_language()

    # ------------------------------------------------------
    async def async_merge_calendar_events(
        self,
    ) -> None:
        """Merge calendar events."""

        self.events = []

        def fix_calendar_name(key: Any) -> str:
            return str(key).replace("calendar.", "").replace("_", " ").capitalize()

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

        for calendar_namr in tmp_events:
            for event in tmp_events[calendar_namr]["events"]:
                self.events.append(
                    CalendarMergeEvent(
                        fix_calendar_name(calendar_namr),
                        event["start"],
                        event["end"],
                        fix_calendar_name(calendar_namr)
                        + "-"
                        + event.get("summary", "")
                        if self.entry.options.get(
                            CONF_CALENDAR_PREFIX_IN_SUMMARY, False
                        )
                        else event.get("summary", ""),
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

                if self.events[index].all_day == self.events[index2].all_day:
                    if (
                        isinstance(self.events[index].start, datetime)
                        and self.events[index].calendar == self.events[index2].calendar
                        and self.events[index].summary == self.events[index2].summary
                        and self.events[index].description
                        == self.events[index2].description
                        and self.events[index].start.time()
                        == self.events[index2].start.time()
                        and self.events[index].end.time()
                        == self.events[index2].end.time()
                    ) or (
                        isinstance(self.events[index].start, date)
                        and self.events[index].calendar == self.events[index2].calendar
                        and self.events[index].summary == self.events[index2].summary
                        and self.events[index].description
                        == self.events[index2].description
                    ):
                        del self.events[index2]

            index += 1

    # ------------------------------------------------------
    def format_date(
        self,
        date_time: datetime | date,
    ) -> str | None:
        """Format date."""
        return babel_format_date(
            date=date_time,
            format=self.entry.options.get(CONF_FORMAT_DATE, "medium"),
            locale=self.language,
        )

    # ------------------------------------------------------
    @async_hass_add_executor_job()
    def async_format_date(
        self,
        date_time: datetime | date,
    ) -> str | None:
        """Format date."""
        return self.format_date(date_time)

    # ------------------------------------------------------
    def format_time(
        self,
        date_time: datetime | time,
    ) -> str | None:
        """Format time."""
        return babel_format_time(
            time=date_time,
            format="short",
            locale=self.language,
        )

    # ------------------------------------------------------
    @async_hass_add_executor_job()
    def async_format_time(
        self,
        date_time: datetime | time,
    ) -> str | None:
        """Format time."""
        return self.format_time(date_time)

    # ------------------------------------------------------
    @async_hass_add_executor_job()
    def async_format_datetime(
        self,
        date_time: datetime | date,
    ) -> str | None:
        """Format datetime."""

        date_str: str = self.format_date(date_time)

        if type(date_time) is date:
            return date_str

        time_str: str = self.format_time(date_time)

        dt_format = babel_get_datetime_format(
            self.entry.options.get(CONF_FORMAT_DATE, "medium"), self.language
        )

        return dt_format.format(time_str, date_str)

    # ------------------------------------------------------
    @async_hass_add_executor_job()
    def async_format_timedelta(
        self,
        time_delta: timedelta,
    ) -> str | None:
        """Format timedelte."""

        return babel_format_timedelta(
            time_delta,
            add_direction=True,
            locale=self.language,
        )

    # ------------------------------------------------------
    async def async_format_event(self, event_num: int) -> str | None:
        """Format event."""

        if event_num < len(self.events):
            tmp_event = self.events[event_num]

            tmp_event.formatted_start = await self.async_format_datetime(
                tmp_event.start
            )
            tmp_event.formatted_start_date = await self.async_format_date(
                tmp_event.start
            )
            tmp_event.formatted_end = await self.async_format_datetime(tmp_event.end)
            tmp_event.formatted_end_date = await self.async_format_date(tmp_event.end)

            if not tmp_event.all_day:
                tmp_event.formatted_start_time = await self.async_format_time(
                    tmp_event.start
                )
                tmp_event.formatted_end_time = await self.async_format_time(
                    tmp_event.end
                )
            else:
                tmp_event.formatted_start_time = await self.async_format_time(
                    time(0, 0)
                )
                tmp_event.formatted_end_time = await self.async_format_time(
                    time(23, 59)
                )

            diff: timedelta = tmp_event.start_datetime_local - dt_util.now()

            if tmp_event.all_day and diff.total_seconds() < 0:
                tmp_event.formatted_time_to = (
                    get_locale(self.language).timeframes.get("now", "now").capitalize()
                )

            else:
                tmp_event.formatted_time_to = await self.async_format_timedelta(diff)

            if self.show_event_as_time_to:
                tmp_event.formatted_event_time = tmp_event.formatted_time_to
            else:
                tmp_event.formatted_event_time = tmp_event.formatted_start

            try:
                value_template: Template | None = Template(
                    str(
                        self.entry.options.get(
                            CONF_EVENT_TEMPLATE, CONF_EVENT_TEMPLATE_DEFAULT
                        )
                    ),
                    self.hass,
                )
                values = {
                    "calendar": tmp_event.calendar,
                    "start": tmp_event.start.isoformat(),
                    "end": tmp_event.end.isoformat(),
                    "all_day": tmp_event.all_day,
                    "summary": tmp_event.summary,
                    "description": tmp_event.description,
                    "location": tmp_event.location,
                    "formatted_start": tmp_event.formatted_start,
                    "formatted_start_date": tmp_event.formatted_start_date,
                    "formatted_start_time": tmp_event.formatted_start_time,
                    "formatted_end": tmp_event.formatted_end,
                    "formatted_end_date": tmp_event.formatted_end_date,
                    "formatted_end_time": tmp_event.formatted_end_time,
                    "formatted_time_to": tmp_event.formatted_time_to,
                    "formatted_event_time": tmp_event.formatted_event_time,
                }

                formatted_event_str = value_template.async_render(values)

            except (TypeError, TemplateError) as e:
                self.create_issue_template(
                    str(e), value_template.template, TRANSLATION_KEY_TEMPLATE_ERROR
                )
                return ""

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
                    "formatted_start_date": replace_markdown_tags(
                        item.formatted_start_date
                    ),
                    "formatted_start_time": replace_markdown_tags(
                        item.formatted_start_time
                    ),
                    "formatted_end": replace_markdown_tags(item.formatted_end),
                    "formatted_end_date": replace_markdown_tags(
                        item.formatted_end_date
                    ),
                    "formatted_end_time": replace_markdown_tags(
                        item.formatted_end_time
                    ),
                    "formatted_time_to": replace_markdown_tags(item.formatted_time_to),
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

    # ------------------------------------------------------------------
    def create_issue(
        self,
        translation_key: str,
        translation_placeholders: dict,
    ) -> None:
        """Create issue on."""

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            DOMAIN_NAME + datetime.now().isoformat(),
            issue_domain=DOMAIN,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=translation_key,
            translation_placeholders=translation_placeholders,
        )

    # ------------------------------------------------------
    async def async_verify_calendar_entities_exist(self) -> bool:
        """Verify calendar entities exist."""
        res: bool = True

        for index, calendar_entity in reversed(list(enumerate(self.calendar_entities))):
            state: State | None = self.hass.states.get(calendar_entity)

            if state is None:
                self.create_issue(
                    calendar_entity,
                    TRANSLATION_KEY_MISSING_CALENDER,
                    {
                        "entity": calendar_entity,
                        "calendar_merge_helper": self.entity_id,
                    },
                )
                del self.calendar_entities[index]
                res = False

        return res
