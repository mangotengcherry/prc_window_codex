"""L3-specific top feature ranking.

The prototype uses a deterministic fallback ranking based on feature/target
correlation. If CatBoost and SHAP are installed later, this module is the only
place that needs model-specific replacement.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.repository import filter_frame


def _feature_target_table(
    frame: pd.DataFrame,
    product_id: str,
    l3_item: str,
    l1_features: list[str],
) -> pd.DataFrame:
    scoped = filter_frame(frame, product_id=product_id, l1_features=l1_features, l3_items=[l3_item])
    wide = scoped.pivot_table(index="wafer_id", columns="l1_feature_name", values="l1_value", aggfunc="first")
    target = (
        scoped.groupby("wafer_id")[["bad_chips", "total_chips"]]
        .first()
        .assign(defect_rate=lambda df: df["bad_chips"] / df["total_chips"])
    )
    return wide.join(target, how="inner").dropna()


def _u_safe_score(feature: pd.Series, target: pd.Series) -> float:
    centered = feature - feature.median()
    candidates = [
        feature,
        centered.abs(),
        centered.pow(2),
    ]
    scores = []
    for candidate in candidates:
        corr = np.corrcoef(candidate.to_numpy(), target.to_numpy())[0, 1]
        scores.append(0.0 if np.isnan(corr) else abs(float(corr)))
    return max(scores)


def rank_l3_features(
    frame: pd.DataFrame,
    product_id: str,
    l3_items: list[str],
    l1_features: list[str],
    min_wafer_count: int = 30,
) -> dict[str, object]:
    by_l3: dict[str, list[dict[str, object]]] = {}
    global_pairs: list[dict[str, object]] = []

    for l3_item in l3_items:
        table = _feature_target_table(frame, product_id, l3_item, l1_features)
        rows = []
        for feature in l1_features:
            if feature not in table.columns:
                continue
            sample_count = int(table[feature].notna().sum())
            if sample_count == 0:
                continue
            score = _u_safe_score(table[feature], table["defect_rate"])
            mean_abs_shap = score
            baseline_ppm = float(table["bad_chips"].sum() / table["total_chips"].sum() * 1_000_000)
            caution_flags = []
            if sample_count < min_wafer_count:
                caution_flags.append("low_sample")
            row = {
                "l3_item_name": l3_item,
                "l1_feature_name": feature,
                "priority_score": round(score, 6),
                "mean_abs_shap": round(mean_abs_shap, 6),
                "u_safe_r2": round(score * score, 6),
                "sample_wafer_count": sample_count,
                "baseline_ppm": round(baseline_ppm, 3),
                "caution_flags": caution_flags,
                "is_numeric_spec_candidate": feature != "time_since_pm",
            }
            rows.append(row)
        rows.sort(key=lambda item: (-item["priority_score"], item["l1_feature_name"]))
        for idx, row in enumerate(rows, 1):
            row["rank"] = idx
        by_l3[l3_item] = rows
        global_pairs.extend(rows)

    global_pairs.sort(key=lambda item: (-item["priority_score"], item["l3_item_name"], item["l1_feature_name"]))
    return {"by_l3": by_l3, "global_pairs": global_pairs}
