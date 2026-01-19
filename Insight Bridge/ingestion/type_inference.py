# ingestion/type_inference.py
from __future__ import annotations

import warnings
from typing import Dict

import pandas as pd

from core.schemas import ColumnSchema, TableSchema


class TypeInference:
    """
    Robust logical type inference:
    - Tries to coerce to numeric first (common CSV issue when read as string).
    - Then datetime, boolean.
    - Fallback categorical.
    Handles high-cardinality, empty columns safely.
    """

    def __init__(self):
        self.high_cardinality_threshold = 50  # For warnings later
        self.numeric_coerce_fraction = 0.95   # >95% coerce to numeric → treat as numeric

    def infer(self, df: pd.DataFrame) -> TableSchema:
        columns: Dict[str, ColumnSchema] = {}

        for col in df.columns:
            original_series = df[col]
            series = original_series.dropna()
            inferred_dtype = str(original_series.dtype)

            logical = "categorical"  # Safe default

            if series.empty:
                logical = "categorical"
            else:
                # 1. Try numeric coercion (critical for CSVs read as string)
                coerced = pd.to_numeric(series, errors="coerce")
                non_na_count = coerced.notna().sum()
                if non_na_count > 0 and (non_na_count / len(series)) >= self.numeric_coerce_fraction:
                    logical = "numeric"
                else:
                    # 2. Datetime parsing
                    if self._try_datetime(series):
                        logical = "datetime"
                    else:
                        # 3. Boolean-like
                        unique_lower = {str(v).lower() for v in series.unique() if pd.notna(v)}
                        bool_set = {"true", "false", "yes", "no", "1", "0", "t", "f"}
                        if unique_lower.issubset(bool_set) and len(unique_lower) <= 2:
                            logical = "boolean"
                        else:
                            # 4. Categorical (including IDs/high-cardinality)
                            logical = "categorical"

            columns[col] = ColumnSchema(
                name=col,
                logical_type=logical,
                inferred_type=inferred_dtype,
                user_override=None,
            )

        return TableSchema(name="inferred", columns=columns)

    def _try_datetime(self, series: pd.Series) -> bool:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(series, errors="coerce")
            return parsed.notna().mean() > 0.7
        except Exception:
            return False