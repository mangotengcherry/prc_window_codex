"""Shared metrics for Process Window calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def defect_ppm(bad_chips: pd.Series | np.ndarray, total_chips: pd.Series | np.ndarray) -> float:
    total = float(np.sum(total_chips))
    if total <= 0:
        return 0.0
    return float(np.sum(bad_chips) / total * 1_000_000)


def production_loss(blocked_wafers: int, population_wafers: int) -> float:
    if population_wafers <= 0:
        return 0.0
    return blocked_wafers / population_wafers


def bootstrap_ppm_ci(
    frame: pd.DataFrame,
    seed: int = 11,
    samples: int = 120,
    low_q: float = 0.05,
    high_q: float = 0.95,
) -> tuple[float, float]:
    if frame.empty:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    values = []
    rows = frame[["bad_chips", "total_chips"]].to_numpy()
    for _ in range(samples):
        idx = rng.integers(0, len(rows), len(rows))
        sample = rows[idx]
        values.append(defect_ppm(sample[:, 0], sample[:, 1]))
    return float(np.quantile(values, low_q)), float(np.quantile(values, high_q))
