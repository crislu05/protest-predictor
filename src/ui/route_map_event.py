"""Event metadata and header card for the route comparison map."""

from __future__ import annotations

import html
import re
from datetime import date, datetime, time

import streamlit as st

from src.database import mapdata
from src.models.labels import TrainingEvent


def historic(event_id: str):
    for he in mapdata.historical_events():
        if he.event_id == event_id:
            return he
    return None


_ORG_PARENS = re.compile(r"\s*\([^)]*\)")


def short_organisation_name(text: str) -> str:
    """Drop parenthetical acronyms so picker labels fit (e.g. ``(PSC)``)."""
    cleaned = _ORG_PARENS.sub("", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def organisation_label(event_id: str) -> str:
    he = historic(event_id)
    if he and he.organiser:
        return short_organisation_name(he.organiser.strip())
    if he and he.name:
        return short_organisation_name(he.name.strip())
    return event_id


def format_clock(value: time | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, datetime):
        return value.time().strftime("%H:%M")
    text = str(value).strip()
    return text[:5] if len(text) >= 5 else text or None


def display_date(iso: str) -> str:
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return iso
    return d.strftime("%d %B %Y").lstrip("0")


def end_time(event_id: str) -> str | None:
    row = (
        mapdata.cursor()
        .execute("SELECT end_time FROM events WHERE event_id = ?", [event_id])
        .fetchone()
    )
    if not row or row[0] is None:
        return None
    return format_clock(row[0])


def schedule_label(event_id: str, he) -> str | None:
    start = he.start_time if he else None
    end = end_time(event_id)
    if start and end:
        return f"{start} to {end}"
    if start:
        return start
    if end:
        return f"Ends {end}"
    return None


def turnout_label(turnout: int | None) -> str:
    if turnout is None:
        return "—"
    if turnout >= 1_000_000:
        return f"{turnout / 1_000_000:.1f}M"
    if turnout >= 10_000:
        return f"{turnout // 1000}k"
    return f"{turnout:,}"


def weather_label(ev: TrainingEvent) -> str:
    precip = float(ev.context.get("precip_mm_4h") or 0)
    if precip < 0.05:
        summary = "Dry"
    elif precip < 2.0:
        summary = "Light rain"
    else:
        summary = "Rain"
    return f"{summary}, {precip:.1f} mm"


def waypoint_stops(he) -> str:
    if not he or not he.waypoints:
        return "—"
    names = [str(n or "").strip() for n, _ in he.waypoints if str(n or "").strip()]
    if not names:
        return "—"
    return " · ".join(names)


def cause_label(cause: str | None) -> str | None:
    if not cause:
        return None
    return cause.replace("_", " ").strip().title()


def event_header(ev: TrainingEvent | None) -> None:
    if ev is None:
        return
    he = historic(ev.event_id)
    org = organisation_label(ev.event_id)
    cause = cause_label(ev.cause or (he.cause if he else None))
    subtitle_parts = [display_date(ev.date)]
    if cause:
        subtitle_parts.append(cause)
    subtitle = " · ".join(subtitle_parts)

    turnout = he.turnout if he else int(ev.context.get("turnout") or 0) or None
    turnout_s = turnout_label(turnout)
    schedule = schedule_label(ev.event_id, he) or "—"
    weather = weather_label(ev)
    stops = waypoint_stops(he)

    with st.container(border=True):
        st.markdown(
            f'<p class="route-event-title">{html.escape(org)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="route-event-sub">{html.escape(subtitle)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="route-event-metrics">
              <div class="route-event-metric">
                <span class="k">Turnout</span>
                <span class="v">{html.escape(turnout_s)}</span>
              </div>
              <div class="route-event-metric">
                <span class="k">Schedule</span>
                <span class="v">{html.escape(schedule)}</span>
              </div>
              <div class="route-event-metric">
                <span class="k">Weather</span>
                <span class="v">{html.escape(weather)}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<p class="route-event-stops-label">Planned stops</p>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="route-event-stops">{html.escape(stops)}</p>',
            unsafe_allow_html=True,
        )


def event_picker_label(event_id: str, by_id: dict[str, TrainingEvent]) -> str:
    ev = by_id.get(event_id)
    if not ev:
        return event_id
    return f"{ev.date}: {organisation_label(event_id)}"
