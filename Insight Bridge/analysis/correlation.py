# analysis/correlation.py
from __future__ import annotations
from typing import List
import pandas as pd


def correlation_matrix(df: pd.DataFrame, numeric_cols: List[str], method: str = "pearson") -> pd.DataFrame:
    """Compute correlation matrix for numeric columns."""
    return df[numeric_cols].corr(method=method)  # Pearson / Spearman etc.[web:119]
