"""Synthetic wafer data for validating known Process Window patterns."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


L1_FEATURES = ["cd_a", "thk_b", "ovl_c", "time_since_pm"]
L3_ITEMS = ["l3_x", "l3_y", "l3_z", "l3_pm"]


def _bad_chips(rng: np.random.Generator, total_chips: int, defect_rate: np.ndarray) -> np.ndarray:
    clipped = np.clip(defect_rate, 0.0001, 0.35)
    return rng.binomial(total_chips, clipped)


def make_synthetic_frame(seed: int = 42, wafers: int = 480) -> pd.DataFrame:
    """Return long-format wafer-level synthetic data with injected patterns."""

    rng = np.random.default_rng(seed)
    product_id = "P_ALPHA"
    total_chips = 1000
    wafer_idx = np.arange(wafers)

    cd_a = rng.normal(45.0, 3.5, wafers)
    thk_b = rng.normal(100.0, 5.0, wafers)
    ovl_c = rng.normal(0.0, 1.0, wafers)
    time_since_pm = rng.uniform(0, 72, wafers)

    l3_x_rate = 0.003 + 0.00055 * (cd_a - 45.0) ** 2
    l3_y_rate = 0.004 + 0.0012 * np.maximum(thk_b - 102.0, 0) ** 2
    risky_cd = cd_a > (46.5 - 1.7 * (ovl_c > 0.6))
    l3_z_rate = 0.004 + np.where(risky_cd & (ovl_c > 0.6), 0.065, 0.002)
    l3_pm_rate = 0.004 + np.where(time_since_pm < 8.0, 0.04, 0.0)

    l3_rates = {
        "l3_x": l3_x_rate,
        "l3_y": l3_y_rate,
        "l3_z": l3_z_rate,
        "l3_pm": l3_pm_rate,
    }
    l1_values = {
        "cd_a": cd_a,
        "thk_b": thk_b,
        "ovl_c": ovl_c,
        "time_since_pm": time_since_pm,
    }
    current_specs = {
        "cd_a": (41.0, 49.0, 45.0),
        "thk_b": (None, 106.0, 100.0),
        "ovl_c": (-1.6, 1.6, 0.0),
        "time_since_pm": (0.0, 72.0, 24.0),
    }

    rows: list[dict[str, object]] = []
    for i in wafer_idx:
        wafer_id = f"W{i:05d}"
        lot_id = f"L{i // 25:04d}"
        for l1_name, l1_series in l1_values.items():
            lower, upper, target = current_specs[l1_name]
            for l3_name, rate in l3_rates.items():
                rows.append(
                    {
                        "product_id": product_id,
                        "wafer_id": wafer_id,
                        "lot_id": lot_id,
                        "measure_time": "2026-06-01",
                        "test_time": "2026-06-03",
                        "process_step": "ETCH",
                        "equipment_id": f"EQP-{i % 4}",
                        "path_id": f"PATH-{i % 3}",
                        "customer_id": f"CUST-{i % 2}",
                        "time_since_pm": float(time_since_pm[i]),
                        "l1_feature_name": l1_name,
                        "l1_value": float(l1_series[i]),
                        "l3_item_name": l3_name,
                        "bad_chips": int(_bad_chips(rng, total_chips, np.array([rate[i]]))[0]),
                        "total_chips": total_chips,
                        "current_lower_spec": None if lower is None else float(lower),
                        "current_upper_spec": None if upper is None else float(upper),
                        "current_target_spec": float(target),
                    }
                )

    return pd.DataFrame(rows)


def write_synthetic_csv(path: str, seed: int = 42, wafers: int = 480) -> None:
    """Create a CSV file that can be loaded by the prototype repository."""

    frame = make_synthetic_frame(seed=seed, wafers=wafers)
    frame.to_csv(path, index=False)
