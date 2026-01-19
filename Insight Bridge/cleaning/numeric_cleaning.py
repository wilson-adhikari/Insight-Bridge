# cleaning/numeric_cleaning.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class NumericCleaningConfig:
    enable_outlier_capping: bool = True
    iqr_multiplier: float = 1.5
    clip_extremes: bool = False  # if True, clip; if False, just leave as is


class NumericCleaner:
    """Numeric-only cleaning: outliers, impossible values, optional clipping."""

    def __init__(self, config: NumericCleaningConfig | None = None) -> None:
        self.config = config or NumericCleaningConfig()

    def clean(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> pd.DataFrame:
        result = df.copy()
        numeric_cols = [c for c, t in dtypes.items() if t == "numeric"]

        if self.config.enable_outlier_capping:
            for col in numeric_cols:
                series = result[col].dropna()
                if series.empty:
                    continue
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - self.config.iqr_multiplier * iqr
                upper = q3 + self.config.iqr_multiplier * iqr
                if self.config.clip_extremes:
                    result[col] = result[col].clip(lower, upper)
                # else: could mark extremes in a separate mask/flag if desired

        # Example placeholder for domain-specific fixes (age, etc.)
        # for col in numeric_cols:
        #     if col.lower() == "age":
        #         result.loc[result[col] < 0, col] = np.nan

        return result
