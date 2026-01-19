# analysis/relationship_explorer.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class NumericCategoricalRelation:
    numeric_col: str
    categorical_col: str
    p_value: float
    effect_size: float | None = None  # placeholder


def anova_hint(df: pd.DataFrame, numeric_col: str, categorical_col: str) -> NumericCategoricalRelation:
    """Very lightweight ANOVA-style hint: low p-value → groups differ."""
    groups = []
    for level, sub in df.groupby(categorical_col):
        vals = sub[numeric_col].dropna()
        if len(vals) > 1:
            groups.append(vals)
    if len(groups) < 2:
        return NumericCategoricalRelation(numeric_col, categorical_col, p_value=1.0)

    f, p = stats.f_oneway(*groups)
    return NumericCategoricalRelation(numeric_col, categorical_col, p_value=float(p))


def scan_numeric_vs_categorical(
    df: pd.DataFrame,
    numeric_cols: List[str],
    categorical_cols: List[str],
) -> List[NumericCategoricalRelation]:
    results: List[NumericCategoricalRelation] = []
    for num in numeric_cols:
        for cat in categorical_cols:
            results.append(anova_hint(df, num, cat))
    return results
