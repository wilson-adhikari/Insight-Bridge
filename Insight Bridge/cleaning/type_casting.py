# cleaning/type_casting.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype


@dataclass
class TypeCastingConfig:
    datetime_format: Optional[str] = None  # optional explicit format
    errors: str = "coerce"                # "raise" | "ignore" | "coerce"


class TypeCaster:
    """Casts raw columns into logical dtypes: numeric, categorical, datetime, bool, ordinal."""

    def __init__(self, config: TypeCastingConfig | None = None) -> None:
        self.config = config or TypeCastingConfig()

    def cast(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> pd.DataFrame:
        """
        dtypes: mapping col -> logical type
        logical types: "numeric", "categorical", "datetime", "boolean", "ordinal"
        """
        result = df.copy()

        for col, t in dtypes.items():
            if col not in result.columns:
                continue

            if t == "numeric":
                result[col] = pd.to_numeric(result[col], errors=self.config.errors)
            elif t == "datetime":
                result[col] = pd.to_datetime(
                    result[col],
                    format=self.config.datetime_format,
                    errors=self.config.errors,
                )
            elif t == "boolean":
                # simple heuristic mapping for booleans
                result[col] = (
                    result[col]
                    .astype("string")
                    .str.strip()
                    .str.lower()
                    .map(
                        {
                            "true": True,
                            "t": True,
                            "yes": True,
                            "y": True,
                            "1": True,
                            "false": False,
                            "f": False,
                            "no": False,
                            "n": False,
                            "0": False,
                        }
                    )
                )
            elif t == "categorical":
                result[col] = result[col].astype("category")
            elif t == "ordinal":
                # here you could plug in ordered categories from config or schema
                cat = CategoricalDtype(ordered=True)
                result[col] = result[col].astype(cat)
            else:
                # unknown: leave as-is
                pass

        return result
