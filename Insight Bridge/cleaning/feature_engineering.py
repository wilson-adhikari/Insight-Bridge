# cleaning/feature_engineering.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

import pandas as pd


ArithmeticOp = Literal["add", "sub", "mul", "div"]
AggFunc = Literal["mean", "median", "sum", "count", "std"]


@dataclass
class ArithmeticFeatureDef:
    name: str
    left_col: str
    right_col: str
    op: ArithmeticOp


@dataclass
class AggregationFeatureDef:
    name: str
    group_col: str
    target_col: str
    func: AggFunc


@dataclass
class FeatureEngineeringConfig:
    arithmetic_features: List[ArithmeticFeatureDef] = field(default_factory=list)
    aggregation_features: List[AggregationFeatureDef] = field(default_factory=list)


class FeatureEngineer:
    """Creates new columns based on simple arithmetic and groupby aggregations."""

    def __init__(self, config: FeatureEngineeringConfig | None = None) -> None:
        self.config = config or FeatureEngineeringConfig()

    def apply(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> pd.DataFrame:
        result = df.copy()

        # Arithmetic features
        for f in self.config.arithmetic_features:
            if f.left_col not in result.columns or f.right_col not in result.columns:
                continue
            left = result[f.left_col]
            right = result[f.right_col]
            if f.op == "add":
                result[f.name] = left + right
            elif f.op == "sub":
                result[f.name] = left - right
            elif f.op == "mul":
                result[f.name] = left * right
            elif f.op == "div":
                result[f.name] = left / right.replace({0: pd.NA})

        # Aggregation features (groupby join back)
        for g in self.config.aggregation_features:
            if g.group_col not in result.columns or g.target_col not in result.columns:
                continue
            grouped = result.groupby(g.group_col)[g.target_col].agg(g.func)
            new_col_name = g.name
            result = result.merge(
                grouped.rename(new_col_name),
                left_on=g.group_col,
                right_index=True,
                how="left",
            )

        return result
