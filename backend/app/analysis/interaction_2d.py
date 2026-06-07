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
    table["x_bin"] = pd.qcut(table[l1_feature_x], q=min(x_bins, len(table)), labels=False, duplicates="drop")
    table["y_bin"] = pd.qcut(table[l1_feature_y], q=min(y_bins, len(table)), labels=False, duplicates="drop")

    cells = []
    for x in range(x_bins):
        for y in range(y_bins):
            group = table[(table["x_bin"] == x) & (table["y_bin"] == y)]
            ppm = defect_ppm(group["bad_chips"], group["total_chips"]) if not group.empty else 0.0
            cells.append(
                {
                    "x_bin": x,
                    "y_bin": y,
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
        "cells": cells,
    }
