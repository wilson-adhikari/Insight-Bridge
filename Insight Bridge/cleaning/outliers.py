# cleaning/outlier_detection.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

import numpy as np
import pandas as pd


Method = Literal["iqr", "zscore"]


@dataclass
class OutlierResult:
    column: str
    method: Method
    indices: List[int]


@dataclass
class OutlierConfig:
    method: Method = "iqr"
    iqr_multiplier: float = 1.5
    z_threshold: float = 3.0
    mark_only: bool = True   # if False, you could drop or clip separately


class OutlierDetector:
    """Standalone outlier detector to feed both cleaning and validation."""

    def __init__(self, config: OutlierConfig | None = None) -> None:
        self.config = config or OutlierConfig()

    def detect(self, df: pd.DataFrame, num_cols: List[str]) -> List[OutlierResult]:
        results: List[OutlierResult] = []

        for col in num_cols:
            s = df[col].dropna()
            if s.empty:
                continue

            if self.config.method == "iqr":
                q1 = s.quantile(0.25)
                q3 = s.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - self.config.iqr_multiplier * iqr
                upper = q3 + self.config.iqr_multiplier * iqr
                mask = (df[col] < lower) | (df[col] > upper)
                idx = df.index[mask].tolist()
            else:  # zscore
                mean = s.mean()
                std = s.std()
                if std == 0:
                    continue
                z = (df[col] - mean) / std
                mask = z.abs() > self.config.z_threshold
                idx = df.index[mask].tolist()

            if idx:
                results.append(OutlierResult(column=col, method=self.config.method, indices=idx))

        return results

    def mark_outliers(self, df: pd.DataFrame, num_cols: List[str]) -> pd.DataFrame:
        """Adds boolean columns col_is_outlier_* as flags."""
        results = self.detect(df, num_cols)
        result_df = df.copy()

        for r in results:
            flag_col = f"{r.column}_is_outlier_{r.method}"
            result_df[flag_col] = False
            result_df.loc[r.indices, flag_col] = True

        return result_df
