"""Shared constants for the route comparison map page."""

from __future__ import annotations

from src.ui.backtest_display import MODEL_LABELS
from src.ui.map_styles import LAYER_PILL_COLORS, MAP_LAYER_STYLES

MAP_LABELS = {
    "route_model": "Route model",
    "shortest_path": MODEL_LABELS["shortest_path"],
    "random_walk": MODEL_LABELS["random_walk"],
}
LAYER_OPTIONS = [
    "Actual",
    "Route model",
    "Shortest path",
    "Random walk",
    "Zone boundary",
    "Restricted zones",
]
DEFAULT_LAYERS = LAYER_OPTIONS[:4]
DECK_TOOLTIP = {"html": "<b>{tooltip}</b>", "style": {"color": "white"}}

_ROUTE_STYLE_KEY: dict[str, str] = {
    "Actual": "actual_casing",
    "Route model": "route_model",
    "Shortest path": "shortest_path",
    "Random walk": "random_walk",
}


def layer_color(label: str) -> str:
    style = _ROUTE_STYLE_KEY.get(label)
    if style:
        return MAP_LAYER_STYLES[style]["hex"]
    return LAYER_PILL_COLORS.get(label, "#64748B")
