<!-- markdownlint-disable MD041 -->
![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/calendar_merge)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/calendar_merge/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/calendar_merge)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/calendar_merge)
[![Validate% with hassfest](https://github.com/kgn3400/calendar_merge/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/calendar_merge/actions/workflows/hassfest.yaml)

<img align="left" width="80" height="80" src="https://kgn3400.github.io/calendar_merge/assets/icon.png" alt="App icon">

# Calendar merge helper

<br/>
The Calendar Merge Helper gives you a complete overview by combining events from one or more calendars. You can set how many days ahead to include and limit the maximum number of events shown.

The helper creates a merged calendar with all relevant events, plus a main sensor that shows the total number of upcoming events. It also provides attributes with both formatted and raw event data, making it easy to generate markdown text or use templates.

Additionally, for each event, an individual sensor is created (with names like _event_0, _event_1, etc.) containing the event summary and date.

Please note: Changes made to the monitored calendars may take a few minutes to appear in the Calendar Merge Helper.

## Installation

For installation search for Calendar merge helper in HACS and download.
Or click
[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=Add%20to%20HACS)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kgn3400&repository=calendar_merge&category=integration)

## Configuration

Configuration is setup via UI in Home assistant. To add one, go to [Settings > Devices & Services > Helpers](https://my.home-assistant.io/redirect/helpers) and click the add button. Next choose the [Calendar merge helper](https://my.home-assistant.io/redirect/config_flow_start?domain=calendar_merge) option.

Or click
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=calendar_merge)
<br>
<!-- <img src="images/config.png" width="400" height="auto" alt="Config1"> -->
<img src="https://kgn3400.github.io/calendar_merge/assets/config1.png" width="400" height="auto" alt="Config 1">
<br/>
<img src="https://kgn3400.github.io/calendar_merge/assets/config2.png" width="400" height="auto" alt="Config 2">
<br/>
<br/>

| State attribute<br/>Template variable| description              | Example                           |
| -------------------- | --------------------- | --------------------------------- |
| calender             | Name of the calendar. | Google Calendar                   |
| start                | Start of the event.   | 2024-07-03T00:21:00+00:00         |
| end                  | End of the event.     | 2024-07-03T00:22:00+00:00         |
| all_day              | All day event.        | false                             |
| summary              | Event summary.        | Home Assistant release party      |
| description          | Event description.    | New features in Home Assistant    |
| location             | Event location.       | Online                            |
| formatted_start      | formatted start.      | Jul 3, 2024, 9:00 PM              |
| formatted_end        | Event location.       | Jul 3, 2024, 10:00 PM             |
| formatted_event_time | Event location.       | in 1 week                            |
| formatted_event      | Event location.       | Home Assistant release party : in 1 week |

It's possible to rotate between multiple Calendar events in the same card by using the [Carousel helper integration](https://github.com/kgn3400/carousel)

## Actions

Available actions: __toggle_show_as_time_to__

### action calendar_merge.toggle_show_as_time_to

Toggle 'Show calendar event as time to' option.
