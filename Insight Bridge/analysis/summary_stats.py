# analysis/summary_stats.py
from __future__ import annotations
from typing import Dict, List
import pandas as pd


def numeric_summary(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """Count, mean, std, min, 25%, 50%, 75%, max for numeric columns."""
    return df[numeric_cols].describe().T  # index = column name[web:101][web:105]


def extended_numeric_summary(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """Adds variance, skewness, kurtosis."""
    desc = df[numeric_cols].describe().T
    desc["var"] = df[numeric_cols].var()
    desc["skew"] = df[numeric_cols].skew()
    desc["kurt"] = df[numeric_cols].kurt()
    return desc
