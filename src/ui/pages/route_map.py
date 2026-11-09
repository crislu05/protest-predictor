"""Streamlit page: compare held-out routes on a London map."""

from __future__ import annotations

import pydeck as pdk
import streamlit as st

from src.config import BACKTEST_PATH
from src.models.backtest import read_backtest
from src.models.graph import MarchGraph
from src.models.labels import TrainingEvent
from src.models.types import BacktestResult, BacktestRow
from src.ui import map_layers
from src.ui.backtest_paths import backtest_has_paths
from src.ui.layout import page_body, section
from src.ui.resources import get_graph, load_training_events
from src.ui.route_map_config import DECK_TOOLTIP
from src.ui.route_map_controls import active_layers_from_session, event_toolbar, map_layer_legend
from src.ui.route_map_deck import (
    context_layers,
    fit_coords_all_routes,
    resolve_map_view,
    route_layers,
    view_state_key,
)
from src.ui.route_map_event import event_header
from src.ui.route_map_metrics import metrics_table


def _events_by_id(
    bt: BacktestResult,
    events: tuple[TrainingEvent, ...],
) -> dict[str, TrainingEvent]:
    ids = {r.event_id for r in bt.rows}
    return {e.event_id: e for e in events if e.event_id in ids}


def _event_ids(bt: BacktestResult) -> list[str]:
    if bt.actual_routes:
        return sorted(bt.actual_routes)
    return sorted({r.event_id for r in bt.rows})


def _row_metrics(bt: BacktestResult, event_id: str) -> dict[str, BacktestRow]:
    return {r.model: r for r in bt.rows if r.event_id == event_id}


def render() -> None:
    """Draw the route comparison map."""
    with page_body():
        st.title("Route comparison")
        bt = read_backtest(BACKTEST_PATH)
        if bt is None or not backtest_has_paths(bt):
            st.warning("No route data for the map.")
            return

        events = list(load_training_events())
        by_id = _events_by_id(bt, tuple(events))
        event_ids = _event_ids(bt)
        if not event_ids:
            st.warning("No events in backtest.")
            return

        g: MarchGraph = get_graph()
        event_id = event_toolbar(event_ids, by_id)
        ev = by_id.get(event_id)
        event_header(ev)

        metrics = _row_metrics(bt, event_id)
        active = active_layers_from_session()
        route_features, layer_fit = route_layers(g, bt, event_id, metrics, active)
        fit_coords = fit_coords_all_routes(g, bt, event_id)
        if not fit_coords:
            fit_coords = layer_fit
        frame_key = view_state_key(event_id, active)

        with section("Route map"):
            map_layer_legend()
            route_deck_layers = map_layers.route_path_and_chevron_layers(route_features)
            if not route_deck_layers:
                st.info("No layers selected.")
            else:
                view = resolve_map_view(fit_coords, g, frame_key)
                under_layers, over_layers = context_layers(active)
                layers = [*under_layers, *route_deck_layers, *over_layers]
                st.pydeck_chart(
                    pdk.Deck(
                        layers=layers,
                        initial_view_state=view,
                        views=[map_layers.map_view_interactive()],
                        map_style=pdk.map_styles.CARTO_LIGHT,
                        map_provider="carto",
                        tooltip=DECK_TOOLTIP,
                    ),
                    height=600,
                    use_container_width=True,
                    key=f"route_map_deck_{frame_key}",
                )

        event_rows = [r for r in bt.rows if r.event_id == event_id]
        if event_rows:
            with section("Metrics for this event"):
                metrics_table(event_rows)


render()
