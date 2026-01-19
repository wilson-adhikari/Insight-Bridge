# analysis/numeric_analysis.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class NumericColumnSummary:
    column: str
    count: int
    mean: float | None
    std: float | None
    min: float | None
    q25: float | None
    median: float | None
    q75: float | None
    max: float | None
    var: float | None
    skew: float | None
    kurt: float | None


@dataclass
class HistogramData:
    column: str
    bin_edges: np.ndarray
    counts: np.ndarray


@dataclass
class NumericAnalysisResult:
    summaries: Dict[str, NumericColumnSummary]
    histograms: Dict[str, HistogramData]


def summarize_numeric(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, NumericColumnSummary]:
    """Return per-column numeric stats (count, mean, median, variance, skew, kurtosis, etc.)."""
    result: Dict[str, NumericColumnSummary] = {}
    sub = df[numeric_cols]

    desc = sub.describe().T  # count, mean, std, min, 25%, 50%, 75%, max[web:137]
    var = sub.var()
    skew = sub.skew()   # skewness of distribution[web:131][web:130]
    kurt = sub.kurt()   # kurtosis (peakedness)[web:134][web:130]

    for col in numeric_cols:
        if col not in desc.index:
            continue
        row = desc.loc[col]
        result[col] = NumericColumnSummary(
            column=col,
            count=int(row["count"]),
            mean=float(row["mean"]) if not pd.isna(row["mean"]) else None,
            std=float(row["std"]) if not pd.isna(row["std"]) else None,
            min=float(row["min"]) if not pd.isna(row["min"]) else None,
            q25=float(row["25%"]) if not pd.isna(row["25%"]) else None,
            median=float(row["50%"]) if not pd.isna(row["50%"]) else None,
            q75=float(row["75%"]) if not pd.isna(row["75%"]) else None,
            max=float(row["max"]) if not pd.isna(row["max"]) else None,
            var=float(var[col]) if col in var and not pd.isna(var[col]) else None,
            skew=float(skew[col]) if col in skew and not pd.isna(skew[col]) else None,
            kurt=float(kurt[col]) if col in kurt and not pd.isna(kurt[col]) else None,
        )

    return result


def histogram_for_column(
    df: pd.DataFrame,
    col: str,
    bins: int = 20,
) -> HistogramData:
    """Compute histogram counts & bin edges for a numeric column (no plotting here)."""
    series = df[col].dropna()
    counts, bin_edges = np.histogram(series, bins=bins)  # numeric binning[web:133][web:129][web:135]
    return HistogramData(column=col, bin_edges=bin_edges, counts=counts)


def analyze_numeric(
    df: pd.DataFrame,
    numeric_cols: List[str],
    bins: int = 20,
) -> NumericAnalysisResult:
    """High-level helper: summaries + histogram data for all numeric columns."""
    summaries = summarize_numeric(df, numeric_cols)
    histograms: Dict[str, HistogramData] = {}

    for col in numeric_cols:
        histograms[col] = histogram_for_column(df, col, bins=bins)

    return NumericAnalysisResult(summaries=summaries, histograms=histograms)
