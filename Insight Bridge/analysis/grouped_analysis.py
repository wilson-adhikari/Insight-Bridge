# analysis/grouped_analysis.py
from __future__ import annotations
from typing import List
import pandas as pd


def grouped_numeric_summary(
    df: pd.DataFrame,
    group_col: str,
    numeric_cols: List[str],
) -> pd.DataFrame:
    agg_df = df.groupby(group_col)[numeric_cols].agg(["count", "mean", "median", "std", "min", "max"])
    return agg_df
