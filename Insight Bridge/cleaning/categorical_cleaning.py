# cleaning/categorical_cleaning.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd


@dataclass
class CategoricalCleaningConfig:
    normalize_case: bool = True
    strip_whitespace: bool = True
    known_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # e.g. {"city": {"NY": "New York", "N.Y.": "New York"}}
    enable_fuzzy_merge_suggestions: bool = False
    fuzzy_threshold: float = 0.85


class CategoricalCleaner:
    """Categorical-only cleaning: normalization and mapping similar labels."""

    def __init__(self, config: CategoricalCleaningConfig | None = None) -> None:
        self.config = config or CategoricalCleaningConfig()

    def clean(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> pd.DataFrame:
        result = df.copy()
        cat_cols = [c for c, t in dtypes.items() if t == "categorical"]

        for col in cat_cols:
            series = result[col].astype("string")

            if self.config.strip_whitespace:
                series = series.str.strip()

            if self.config.normalize_case:
                series = series.str.title()

            mapping = self.config.known_mappings.get(col, {})
            if mapping:
                series = series.replace(mapping)

            result[col] = series

            # Fuzzy suggestion is UI-level; here we could compute candidate pairs if enabled.
            # Leaving out heavy logic to keep this as a clean skeleton.

        return result
