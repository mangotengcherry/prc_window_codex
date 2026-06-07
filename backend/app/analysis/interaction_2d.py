"""2D interaction heatmap data generation."""

from __future__ import annotations

import pandas as pd

from app.analysis.metrics import defect_ppm
from app.repository import filter_frame


def build_interaction_heatmap(
    frame: pd.DataFrame,
    product_id: str,
    l1_feature_x: str,
    l1_feature_y: str,
    l3_item_name: str,
    x_bins: int = 6,
    y_bins: int = 6,
    min_wafer_count: int = 12,
) -> dict[str, object]:
    scoped = filter_frame(frame, product_id=product_id, l1_features=[l1_feature_x, l1_feature_y], l3_items=[l3_item_name])
    wide = scoped.pivot_table(index="wafer_id", columns="l1_feature_name", values="l1_value", aggfunc="first")
    target = scoped.groupby("wafer_id")[["bad_chips", "total_chips"]].first()
    table = wide.join(target, how="inner").dropna()
    table["x_bin"], x_edges = pd.qcut(
        table[l1_feature_x],
        q=min(x_bins, len(table)),
        labels=False,
        duplicates="drop",
        retbins=True,
    )
    table["y_bin"], y_edges = pd.qcut(
        table[l1_feature_y],
        q=min(y_bins, len(table)),
        labels=False,
        duplicates="drop",
        retbins=True,
    )
    actual_x_bins = max(int(table["x_bin"].max()) + 1, 0) if not table.empty else 0
    actual_y_bins = max(int(table["y_bin"].max()) + 1, 0) if not table.empty else 0

    cells = []
    for x in range(actual_x_bins):
        for y in range(actual_y_bins):
            group = table[(table["x_bin"] == x) & (table["y_bin"] == y)]
            ppm = defect_ppm(group["bad_chips"], group["total_chips"]) if not group.empty else 0.0
            x_min = float(x_edges[x])
            x_max = float(x_edges[x + 1])
            y_min = float(y_edges[y])
            y_max = float(y_edges[y + 1])
            cells.append(
                {
                    "x_bin": x,
                    "y_bin": y,
                    "x_center": round((x_min + x_max) / 2, 4),
                    "y_center": round((y_min + y_max) / 2, 4),
                    "x_min": round(x_min, 4),
                    "x_max": round(x_max, 4),
                    "y_min": round(y_min, 4),
                    "y_max": round(y_max, 4),
                    "wafer_count": int(len(group)),
                    "defect_ppm": round(ppm, 3),
                    "volume_share": round(len(group) / len(table), 6) if len(table) else 0.0,
                    "unreliable": len(group) < min_wafer_count,
                }
            )

    return {
        "product_id": product_id,
        "l1_feature_x": l1_feature_x,
        "l1_feature_y": l1_feature_y,
        "l3_item_name": l3_item_name,
        "x_bin_count": actual_x_bins,
        "y_bin_count": actual_y_bins,
        "cells": cells,
    }
