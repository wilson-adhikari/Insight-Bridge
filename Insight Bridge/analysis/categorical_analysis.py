# analysis/categorical_analysis.py
from __future__ import annotations
from typing import Dict, List, Tuple
import pandas as pd


def freq_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    vc = df[col].value_counts(dropna=False)
    return pd.DataFrame({"count": vc, "fraction": vc / len(df)})


def top_categories(df: pd.DataFrame, col: str, top_n: int = 5) -> pd.DataFrame:
    return freq_table(df, col).head(top_n)


def imbalance_score(df: pd.DataFrame, col: str) -> float:
    vc = df[col].value_counts(dropna=False)
    if vc.empty:
        return 0.0
    return float(vc.iloc[0] / len(df))


def crosstab_two(df: pd.DataFrame, col_a: str, col_b: str, normalize: str | None = None) -> pd.DataFrame:
    """Cross-tab between two categoricals with optional normalization ('index', 'columns', 'all')."""
    return pd.crosstab(df[col_a], df[col_b], normalize=normalize)
