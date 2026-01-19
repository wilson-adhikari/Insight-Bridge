# cleaning/missing_value_handler.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any

import pandas as pd


@dataclass
class MissingStrategyConfig:
    strategy: str = "auto"          # "drop", "mean", "median", "mode", "ffill", "bfill", "constant", "by_group"
    constant_value: Optional[Any] = None
    group_by: Optional[str] = None  # column name for conditional filling


class MissingValueHandler:
    """Unified missing-value handling for numeric and categorical columns."""

    def apply(
        self,
        df: pd.DataFrame,
        dtypes: Dict[str, str],
        strategies: Dict[str, MissingStrategyConfig],
    ) -> pd.DataFrame:
        result = df.copy()

        for col in result.columns:
            col_type = dtypes.get(col, "unknown")
            cfg = strategies.get(col, MissingStrategyConfig())

            if cfg.strategy == "drop":
                result = result.dropna(subset=[col])
                continue

            if cfg.strategy == "mean" and col_type == "numeric":
                result[col] = result[col].fillna(result[col].mean())
            elif cfg.strategy == "median" and col_type == "numeric":
                result[col] = result[col].fillna(result[col].median())
            elif cfg.strategy == "mode":
                if not result[col].mode().empty:
                    result[col] = result[col].fillna(result[col].mode().iloc[0])
            elif cfg.strategy == "ffill":
                result[col] = result[col].fillna(method="ffill")
            elif cfg.strategy == "bfill":
                result[col] = result[col].fillna(method="bfill")
            elif cfg.strategy == "constant":
                result[col] = result[col].fillna(cfg.constant_value)
            elif cfg.strategy == "by_group" and cfg.group_by:
                result[col] = (
                    result.groupby(cfg.group_by)[col]
                    .transform(lambda s: s.fillna(s.median() if col_type == "numeric" else s.mode().iloc[0] if not s.mode().empty else s))
                )
            else:
                # auto default
                if col_type == "numeric":
                    result[col] = result[col].fillna(result[col].median())
                else:
                    if not result[col].mode().empty:
                        result[col] = result[col].fillna(result[col].mode().iloc[0])

        return result
