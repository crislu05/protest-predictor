"""Layer legend and event navigation for the route comparison map."""

from __future__ import annotations

import html

import streamlit as st

from src.models.labels import TrainingEvent
from src.ui.route_map_config import DEFAULT_LAYERS, LAYER_OPTIONS, layer_color
from src.ui.route_map_event import event_picker_label


def active_layers_from_session() -> set[str]:
    active: set[str] = set()
    for opt in LAYER_OPTIONS:
        key = f"layer_toggle_{opt}"
        if st.session_state.get(key, opt in DEFAULT_LAYERS):
            active.add(opt)
    return active or set(DEFAULT_LAYERS)


def _legend_swatch_html(opt: str, color: str) -> str:
    if opt == "Restricted zones":
        return (
            f'<span class="map-legend-square" style="background:{color};'
            f'border:1px solid #DC2626"></span>'
        )
    return f'<span class="map-legend-swatch" style="color:{color}">━</span>'


def map_layer_legend() -> None:
    """Coloured swatch + label with a checkbox for each map layer."""
    st.markdown('<span class="map-legend-marker"></span>', unsafe_allow_html=True)
    col_widths = [1.0, 1.05, 1.12, 1.0, 1.18, 1.32]
    cols = st.columns(col_widths, gap="small", vertical_alignment="center")
    for col, opt in zip(cols, LAYER_OPTIONS, strict=True):
        color = layer_color(opt)
        key = f"layer_toggle_{opt}"
        default = opt in DEFAULT_LAYERS
        with col:
            pick, label = st.columns([0.11, 0.89], gap="small", vertical_alignment="center")
            with pick:
                st.checkbox(
                    "on",
                    value=default,
                    key=key,
                    label_visibility="collapsed",
                )
            with label:
                st.markdown(
                    f'<span class="map-legend-label">'
                    f"{_legend_swatch_html(opt, color)}"
                    f"<span>{html.escape(opt)}</span></span>",
                    unsafe_allow_html=True,
                )


def event_toolbar(event_ids: list[str], by_id: dict[str, TrainingEvent]) -> str:
    if "map_event" not in st.session_state and event_ids:
        st.session_state["map_event"] = event_ids[0]
    event_id = st.session_state.get("map_event", event_ids[0])
    if event_id not in event_ids:
        event_id = event_ids[0]
        st.session_state["map_event"] = event_id
    idx = event_ids.index(event_id)
    label = event_picker_label(event_id, by_id)

    st.markdown('<span class="route-event-nav-marker"></span>', unsafe_allow_html=True)
    nav = st.columns([1.1, 4, 1.1], gap="medium", vertical_alignment="center")
    with nav[0]:
        if st.button(
            "◀  Previous",
            disabled=idx <= 0,
            use_container_width=True,
            type="secondary",
            key="map_event_prev",
        ):
            st.session_state["map_event"] = event_ids[idx - 1]
            st.rerun()
    with nav[1]:
        st.markdown(
            f'<p class="route-event-nav-title">{html.escape(label)}</p>',
            unsafe_allow_html=True,
        )
    with nav[2]:
        if st.button(
            "Next  ▶",
            disabled=idx >= len(event_ids) - 1,
            use_container_width=True,
            type="secondary",
            key="map_event_next",
        ):
            st.session_state["map_event"] = event_ids[idx + 1]
            st.rerun()
    return event_id
