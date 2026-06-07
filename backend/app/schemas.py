"""Pydantic schemas for the Process Window API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RankRequest(BaseModel):
    product_id: str = "P_ALPHA"
    selected_l3_items: list[str] = Field(default_factory=lambda: ["l3_x", "l3_y", "l3_z"])
    selected_l1_features: list[str] = Field(default_factory=lambda: ["cd_a", "thk_b", "ovl_c", "time_since_pm"])
    min_wafer_count: int = 30


class SingleAnalysisRequest(BaseModel):
    product_id: str = "P_ALPHA"
    l1_feature_name: str = "cd_a"
    l3_item_name: str = "l3_x"
    bin_count: int = 10
    min_wafer_count: int = 30
    max_allowed_loss_rate: float = 0.4


class InteractionRequest(BaseModel):
    product_id: str = "P_ALPHA"
    l1_feature_x: str = "cd_a"
    l1_feature_y: str = "ovl_c"
    l3_item_name: str = "l3_z"
    x_bins: int = 6
    y_bins: int = 6
    min_wafer_count: int = 12


class GenericResponse(BaseModel):
    data: dict[str, Any]
