"""Data loading and catalog helpers for the prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "product_id",
    "wafer_id",
    "lot_id",
    "l1_feature_name",
    "l1_value",
    "l3_item_name",
    "bad_chips",
    "total_chips",
}


def validate_frame(frame: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if (frame["total_chips"] <= 0).any():
        raise ValueError("total_chips must be positive")
    duplicates = frame.duplicated(["wafer_id", "l1_feature_name", "l3_item_name"])
    if duplicates.any():
        raise ValueError("Duplicate wafer/l1/l3 rows found")


def load_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    validate_frame(frame)
    return frame


def filter_frame(
    frame: pd.DataFrame,
    product_id: str | None = None,
    l1_features: Iterable[str] | None = None,
    l3_items: Iterable[str] | None = None,
) -> pd.DataFrame:
    filtered = frame
    if product_id:
        filtered = filtered[filtered["product_id"] == product_id]
    if l1_features:
        filtered = filtered[filtered["l1_feature_name"].isin(list(l1_features))]
    if l3_items:
        filtered = filtered[filtered["l3_item_name"].isin(list(l3_items))]
    return filtered.copy()


@dataclass
class SyntheticRepository:
    """Small repository wrapper used by tests and API endpoints."""

    frame: pd.DataFrame

    def __post_init__(self) -> None:
        validate_frame(self.frame)

    def get_catalog(self) -> dict[str, object]:
        specs = (
            self.frame.groupby("l1_feature_name")[
                ["current_lower_spec", "current_upper_spec", "current_target_spec"]
            ]
            .first()
            .where(pd.notna, None)
            .to_dict(orient="index")
        )
        return {
            "products": sorted(self.frame["product_id"].unique().tolist()),
            "l1_features": sorted(self.frame["l1_feature_name"].unique().tolist()),
            "l3_items": sorted(self.frame["l3_item_name"].unique().tolist()),
            "filters": {
                "equipment_id": sorted(self.frame.get("equipment_id", pd.Series()).dropna().unique().tolist()),
                "path_id": sorted(self.frame.get("path_id", pd.Series()).dropna().unique().tolist()),
                "customer_id": sorted(self.frame.get("customer_id", pd.Series()).dropna().unique().tolist()),
            },
            "current_specs": specs,
        }

    def load_frame(self) -> pd.DataFrame:
        return self.frame.copy()
