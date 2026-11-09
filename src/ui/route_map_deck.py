"""Deck.gl layers and view framing for the route comparison map."""

from __future__ import annotations

import pydeck as pdk
import streamlit as st

from src.config import DB_PATH
from src.database import mapdata
from src.database.types import LonLat
from src.models.graph import MarchGraph
from src.models.types import BacktestResult, BacktestRow
from src.ui import map_layers
from src.ui.backtest_paths import paths_for_event
from src.ui.map_styles import MAP_LAYER_STYLES
from src.ui.route_map_config import MAP_LABELS


def context_layers(active: set[str]) -> tuple[list[pdk.Layer], list[pdk.Layer]]:
    under: list[pdk.Layer] = []
    over: list[pdk.Layer] = []
    if not DB_PATH.is_file():
        return under, over
    try:
        if "Restricted zones" in active:
            zones = mapdata.legal_zones()
            if zones:
                under.extend(map_layers.legal_zone_layers(zones))
        if "Zone boundary" in active:
            over.extend(
                map_layers.ring_outline_layers(
                    mapdata.boundary(),
                    [156, 163, 175, 200],
                    width=3,
                )
            )
    except OSError:
        pass
    return under, over


def route_layers(
    g: MarchGraph,
    bt: BacktestResult,
    event_id: str,
    metrics: dict[str, BacktestRow],
    active: set[str],
) -> tuple[list[dict], list[LonLat]]:
    features: list[dict] = []
    fit_coords: list[LonLat] = []
    paths = paths_for_event(bt, event_id)
    actual = (bt.actual_routes or {}).get(event_id, [])

    def add_route(
        model_key: str | None,
        ids: list[str],
        style_key: str,
        name: str,
    ) -> None:
        stl = MAP_LAYER_STYLES[style_key]
        row = metrics.get(model_key) if model_key else None
        overlap = row.top1_jaccard if row else None
        features.extend(
            map_layers.route_path_features(
                g,
                ids,
                stl["hex"],
                stl["width"],
                name,
                overlap=overlap,
                n_steps=len(ids),
                dash_array=stl["dash"],
                alpha=stl["alpha"],
                trim_backtrack=style_key == "actual_casing",
            )
        )
        fit_coords.extend(map_layers.coords_for_fit(g, ids))

    if "Actual" in active and actual:
        add_route(None, actual, "actual_casing", "Actual")
    if "Shortest path" in active and "shortest_path" in paths:
        add_route(
            "shortest_path", paths["shortest_path"], "shortest_path", MAP_LABELS["shortest_path"]
        )
    if "Random walk" in active and "random_walk" in paths:
        add_route("random_walk", paths["random_walk"], "random_walk", MAP_LABELS["random_walk"])
    if "Route model" in active and "route_model" in paths:
        add_route("route_model", paths["route_model"], "route_model", MAP_LABELS["route_model"])
    return features, fit_coords


def fit_coords_all_routes(
    g: MarchGraph,
    bt: BacktestResult,
    event_id: str,
) -> list[LonLat]:
    paths = paths_for_event(bt, event_id)
    actual = (bt.actual_routes or {}).get(event_id, [])
    fit: list[LonLat] = []
    for ids in (
        actual,
        paths.get("shortest_path"),
        paths.get("random_walk"),
        paths.get("route_model"),
    ):
        if ids:
            fit.extend(map_layers.coords_for_fit(g, ids))
    return fit


def view_state_key(event_id: str, active: set[str]) -> str:
    return f"{event_id}|{'|'.join(sorted(active))}"


def resolve_map_view(fit_coords: list[LonLat], g: MarchGraph, frame_key: str) -> pdk.ViewState:
    reset = st.session_state.pop("map_reset_view", False)
    reframe = reset or st.session_state.get("map_frame_key") != frame_key
    if reframe:
        st.session_state["map_frame_key"] = frame_key
        default = map_layers.view_state_for_coords(fit_coords)
        if default is None:
            if fit_coords:
                span = max(
                    max(c[0] for c in fit_coords) - min(c[0] for c in fit_coords),
                    max(c[1] for c in fit_coords) - min(c[1] for c in fit_coords),
                )
                if span > map_layers.MAX_ROUTE_SPAN_DEG:
                    st.error("Could not frame this route on the map.")
            default = map_layers.initial_view_state(g)
        st.session_state["map_default_view"] = default
    return st.session_state.get("map_default_view", map_layers.initial_view_state(g))
