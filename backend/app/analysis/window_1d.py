"""Single L1 vs L3 Process Window analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analysis.metrics import bootstrap_ppm_ci, defect_ppm, production_loss
from app.repository import filter_frame


def _analysis_table(frame: pd.DataFrame, product_id: str, l1_feature_name: str, l3_item_name: str) -> pd.DataFrame:
    scoped = filter_frame(frame, product_id=product_id, l1_features=[l1_feature_name], l3_items=[l3_item_name])
    return scoped.dropna(subset=["l1_value"]).copy()


def _bin_rows(table: pd.DataFrame, bin_count: int) -> list[dict[str, object]]:
    binned = table.copy()
    binned["bin"] = pd.qcut(binned["l1_value"], q=min(bin_count, len(binned)), duplicates="drop")
    rows = []
    for interval, group in binned.groupby("bin", observed=True):
        low_ci, high_ci = bootstrap_ppm_ci(group)
        rows.append(
            {
                "bin_label": str(interval),
                "l1_min": round(float(group["l1_value"].min()), 4),
                "l1_max": round(float(group["l1_value"].max()), 4),
                "wafer_count": int(len(group)),
                "defect_ppm": round(defect_ppm(group["bad_chips"], group["total_chips"]), 3),
                "ci_low_ppm": round(low_ci, 3),
                "ci_high_ppm": round(high_ci, 3),
                "volume_share": round(len(group) / len(table), 6),
            }
        )
    return rows


def _evaluate_window(table: pd.DataFrame, lower: float | None, upper: float | None) -> dict[str, float]:
    mask = pd.Series(True, index=table.index)
    if lower is not None:
        mask &= table["l1_value"] >= lower
    if upper is not None:
        mask &= table["l1_value"] <= upper
    passed = table[mask]
    blocked = len(table) - len(passed)
    baseline = defect_ppm(table["bad_chips"], table["total_chips"])
    residual = defect_ppm(passed["bad_chips"], passed["total_chips"]) if not passed.empty else baseline
    return {
        "pass_wafer_count": int(len(passed)),
        "pass_rate": len(passed) / len(table),
        "production_loss": production_loss(blocked, len(table)),
        "residual_ppm": residual,
        "ppm_improvement": baseline - residual,
        "target": float(passed["l1_value"].median()) if not passed.empty else float(table["l1_value"].median()),
    }


def _candidate_specs(
    table: pd.DataFrame,
    min_wafer_count: int,
    max_allowed_loss_rate: float,
) -> list[dict[str, object]]:
    quantiles = np.quantile(table["l1_value"], np.linspace(0.1, 0.9, 9))
    candidates: list[dict[str, object]] = []

    for upper in quantiles:
        metrics = _evaluate_window(table, None, float(upper))
        candidates.append({"lower": None, "upper": float(upper), **metrics})
    for lower in quantiles:
        metrics = _evaluate_window(table, float(lower), None)
        candidates.append({"lower": float(lower), "upper": None, **metrics})

    centered = float(table.loc[table["bad_chips"].idxmin(), "l1_value"])
    for width in np.linspace(1.0, 8.0, 15):
        lower = centered - width / 2
        upper = centered + width / 2
        metrics = _evaluate_window(table, lower, upper)
        candidates.append({"lower": lower, "upper": upper, **metrics})

    filtered = []
    for row in candidates:
        if row["pass_wafer_count"] < min_wafer_count:
            continue
        if row["production_loss"] > max_allowed_loss_rate:
            continue
        row["spec_score"] = row["ppm_improvement"] * row["pass_rate"]
        if row["ppm_improvement"] <= 0:
            continue
        filtered.append(row)

    filtered.sort(key=lambda item: (-item["spec_score"], item["production_loss"]))
    for row in filtered:
        for key in ["lower", "upper", "target", "pass_rate", "production_loss", "residual_ppm", "ppm_improvement", "spec_score"]:
            if row[key] is not None:
                row[key] = round(float(row[key]), 6)
    return filtered[:10]


def analyze_single_window(
    frame: pd.DataFrame,
    product_id: str,
    l1_feature_name: str,
    l3_item_name: str,
    bin_count: int = 10,
    min_wafer_count: int = 30,
    max_allowed_loss_rate: float = 0.35,
) -> dict[str, object]:
    table = _analysis_table(frame, product_id, l1_feature_name, l3_item_name)
    if table.empty:
        raise ValueError("No rows for selected product/L1/L3")

    bins = _bin_rows(table, bin_count)
    baseline_ppm = defect_ppm(table["bad_chips"], table["total_chips"])
    candidates = _candidate_specs(table, min_wafer_count, max_allowed_loss_rate)
    return {
        "product_id": product_id,
        "l1_feature_name": l1_feature_name,
        "l3_item_name": l3_item_name,
        "analysis_population_wafers": int(len(table)),
        "baseline_ppm": round(baseline_ppm, 3),
        "bins": bins,
        "candidate_specs": candidates,
        "denominators": {"production_loss": "wafer", "defect_ppm": "chip"},
    }
