"""Per-event metrics table on the route comparison map."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.models.types import BacktestRow
from src.ui.map_styles import MAP_LAYER_STYLES
from src.ui.route_map_config import MAP_LABELS


def metrics_table(rows: list[BacktestRow]) -> None:
    df = pd.DataFrame(
        [
            {
                "model_id": r.model,
                "Model": MAP_LABELS.get(r.model, r.model),
                "swatch": MAP_LAYER_STYLES.get(r.model, MAP_LAYER_STYLES["route_model"])["hex"],
                "Mean log-likelihood": r.mean_log_likelihood,
                "Route overlap": (
                    float(r.top1_jaccard) * 100.0 if r.top1_jaccard is not None else None
                ),
            }
            for r in rows
        ]
    )
    best_ll = df["Mean log-likelihood"].max()
    best_ov = df["Route overlap"].max()
    winner_ids = set(
        df.loc[
            (df["Mean log-likelihood"] == best_ll) | (df["Route overlap"] == best_ov), "model_id"
        ]
    )
    swatches = list(df["swatch"])

    def model_border(_series: pd.Series) -> list[str]:
        return [f"border-left: 4px solid {c}; padding-left: 6px" for c in swatches]

    show = df.drop(columns=["model_id", "swatch"])

    def row_bg(row: pd.Series) -> list[str]:
        mid = df.loc[row.name, "model_id"]
        bg = "background-color: #F8FAFC" if mid in winner_ids else ""
        return [bg] * len(row)

    styled = (
        show.style.format(
            {
                "Mean log-likelihood": "{:.4f}",
                "Route overlap": "{:.1f}%",
            }
        )
        .bar(subset=["Route overlap"], color="#E2E8F0", vmin=0, vmax=100)
        .apply(model_border, subset=["Model"])
        .apply(row_bg, axis=1)
        .apply(
            lambda col: [
                "font-weight:700"
                if (col.name == "Mean log-likelihood" and v == best_ll)
                or (col.name == "Route overlap" and v == best_ov)
                else ""
                for v in col
            ],
            axis=0,
        )
    )
    st.dataframe(
        styled,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Model": st.column_config.TextColumn("Model"),
            "Mean log-likelihood": st.column_config.NumberColumn(
                "Mean log-likelihood",
                format="%.4f",
            ),
            "Route overlap": st.column_config.ProgressColumn(
                "Route overlap",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )
