# cleaning/validators.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass
class ImbalanceWarning:
    column: str
    top_category: str
    top_fraction: float


@dataclass
class OutlierWarning:
    column: str
    n_outliers: int


@dataclass
class MissingExtremesWarning:
    column: str
    note: str


@dataclass
class ValidationReport:
    imbalance_warnings: List[ImbalanceWarning] = field(default_factory=list)
    outlier_warnings: List[OutlierWarning] = field(default_factory=list)
    missing_extremes_warnings: List[MissingExtremesWarning] = field(default_factory=list)


class DataValidator:
    """Computes simple quality warnings for numeric & categorical columns."""

    def __init__(
        self,
        imbalance_threshold: float = 0.9,
        outlier_iqr_multiplier: float = 1.5,
    ) -> None:
        self.imbalance_threshold = imbalance_threshold
        self.outlier_iqr_multiplier = outlier_iqr_multiplier

    def validate(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> ValidationReport:
        rep = ValidationReport()

        cat_cols = [c for c, t in dtypes.items() if t == "categorical"]
        num_cols = [c for c, t in dtypes.items() if t == "numeric"]

        # Imbalance
        for col in cat_cols:
            vc = df[col].value_counts(dropna=False)
            if vc.empty:
                continue
            top_cat = vc.index[0]
            top_frac = vc.iloc[0] / len(df)
            if top_frac >= self.imbalance_threshold:
                rep.imbalance_warnings.append(
                    ImbalanceWarning(column=col, top_category=str(top_cat), top_fraction=float(top_frac))
                )

        # Outliers (IQR-based count)
        for col in num_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - self.outlier_iqr_multiplier * iqr
            upper = q3 + self.outlier_iqr_multiplier * iqr
            mask = (series < lower) | (series > upper)
            n_outliers = int(mask.sum())
            if n_outliers > 0:
                rep.outlier_warnings.append(OutlierWarning(column=col, n_outliers=n_outliers))

        # Missing extremes (rough heuristic)
        for col in num_cols:
            series = df[col]
            if series.isna().any():
                # if dropping NA changes min/max a lot, warn
                min_full = series.min()
                max_full = series.max()
                min_no_na = series.dropna().min()
                max_no_na = series.dropna().max()
                if not np.isclose(min_full, min_no_na) or not np.isclose(max_full, max_no_na):
                    rep.missing_extremes_warnings.append(
                        MissingExtremesWarning(
                            column=col,
                            note="Min/Max influenced by missing values; consider checking boundary NAs.",
                        )
                    )

        return rep
