# cleaning/encoding.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

import pandas as pd


EncodingType = Literal["one_hot", "ordinal", "frequency"]


@dataclass
class ColumnEncodingConfig:
    encoding: EncodingType = "one_hot"
    # For ordinal only:
    ordered_categories: Optional[List[str]] = None
    # For one-hot high-cardinality:
    min_freq: Optional[int] = None     # below → "Other"
    min_freq_fraction: Optional[float] = None  # alternative: fraction threshold


@dataclass
class EncodingConfig:
    per_column: Dict[str, ColumnEncodingConfig] = field(default_factory=dict)
    default_encoding: EncodingType = "one_hot"
    high_cardinality_threshold: int = 30  # suggest ordinal/frequency above this


class Encoder:
    """Encodes categorical columns for ML (one-hot, ordinal, frequency)."""

    def __init__(self, config: EncodingConfig | None = None) -> None:
        self.config = config or EncodingConfig()
        # store category maps for inverse transform if needed
        self.ordinal_maps: Dict[str, Dict[str, int]] = {}
        self.freq_maps: Dict[str, Dict[str, float]] = {}

    def fit_transform(self, df: pd.DataFrame, cat_cols: List[str]) -> pd.DataFrame:
        result = df.copy()

        for col in cat_cols:
            cfg = self.config.per_column.get(
                col,
                ColumnEncodingConfig(encoding=self.config.default_encoding),
            )
            series = result[col].astype("string")

            if cfg.encoding == "one_hot":
                result = self._apply_one_hot(result, col, series, cfg)
            elif cfg.encoding == "ordinal":
                result = self._apply_ordinal(result, col, series, cfg)
            elif cfg.encoding == "frequency":
                result = self._apply_frequency(result, col, series, cfg)

        return result

    def _apply_one_hot(
        self,
        df: pd.DataFrame,
        col: str,
        series: pd.Series,
        cfg: ColumnEncodingConfig,
    ) -> pd.DataFrame:
        vc = series.value_counts()
        if cfg.min_freq is not None or cfg.min_freq_fraction is not None:
            # collapse rare categories
            total = len(series)
            def is_rare(cat: str) -> bool:
                count = vc.get(cat, 0)
                if cfg.min_freq is not None and count < cfg.min_freq:
                    return True
                if cfg.min_freq_fraction is not None and (count / total) < cfg.min_freq_fraction:
                    return True
                return False

            series = series.where(~series.isin([c for c in vc.index if is_rare(c)]), other="Other")

        dummies = pd.get_dummies(series, prefix=col)
        df = df.drop(columns=[col]).join(dummies)
        return df

    def _apply_ordinal(
        self,
        df: pd.DataFrame,
        col: str,
        series: pd.Series,
        cfg: ColumnEncodingConfig,
    ) -> pd.DataFrame:
        if cfg.ordered_categories:
            cats = cfg.ordered_categories
        else:
            cats = list(series.dropna().unique())

        mapping = {cat: i for i, cat in enumerate(cats)}
        self.ordinal_maps[col] = mapping
        df[col] = series.map(mapping).astype("float")
        return df

    def _apply_frequency(
        self,
        df: pd.DataFrame,
        col: str,
        series: pd.Series,
        cfg: ColumnEncodingConfig,
    ) -> pd.DataFrame:
        freq = series.value_counts(normalize=True)
        mapping = freq.to_dict()
        self.freq_maps[col] = mapping
        df[col] = series.map(mapping).fillna(0.0)
        return df
