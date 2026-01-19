# cleaning/preprocessor.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

import pandas as pd

from .missing_value_handler import MissingValueHandler, MissingStrategyConfig
from .numeric_cleaning import NumericCleaner, NumericCleaningConfig
from .categorical_cleaning import CategoricalCleaner, CategoricalCleaningConfig
from .feature_engineering import FeatureEngineer, FeatureEngineeringConfig
from .validators import DataValidator, ValidationReport


@dataclass
class CleaningConfig:
    missing_strategies: Dict[str, MissingStrategyConfig] = field(default_factory=dict)
    numeric_config: NumericCleaningConfig = field(default_factory=NumericCleaningConfig)
    categorical_config: CategoricalCleaningConfig = field(default_factory=CategoricalCleaningConfig)
    feature_config: FeatureEngineeringConfig = field(default_factory=FeatureEngineeringConfig)


@dataclass
class CleaningReport:
    initial_shape: tuple
    final_shape: tuple
    applied_steps: List[str]
    validation_report: Optional[ValidationReport] = None
    notes: List[str] = field(default_factory=list)


class Preprocessor:
    """High-level cleaner that coordinates missing values, numeric + categorical cleaning,
    feature engineering, and validation for a pandas DataFrame."""

    def __init__(self, config: Optional[CleaningConfig] = None) -> None:
        self.config = config or CleaningConfig()
        self._missing_handler = MissingValueHandler()
        self._numeric_cleaner = NumericCleaner(self.config.numeric_config)
        self._categorical_cleaner = CategoricalCleaner(self.config.categorical_config)
        self._feature_engineer = FeatureEngineer(self.config.feature_config)
        self._validator = DataValidator()

    def clean(self, df: pd.DataFrame, dtypes: Dict[str, str]) -> tuple[pd.DataFrame, CleaningReport]:
        """
        Parameters
        ----------
        df : DataFrame
            Input raw dataframe (will not be modified in-place).
        dtypes : dict
            Mapping col -> logical type ("numeric", "categorical", "datetime", "boolean", "ordinal").

        Returns
        -------
        cleaned_df, report
        """
        report = CleaningReport(
            initial_shape=df.shape,
            final_shape=df.shape,
            applied_steps=[],
        )
        work_df = df.copy()

        # 1) Missing values (for all columns)
        work_df = self._missing_handler.apply(work_df, dtypes, self.config.missing_strategies)
        report.applied_steps.append("missing_values")

        # 2) Numeric-specific cleaning
        work_df = self._numeric_cleaner.clean(work_df, dtypes)
        report.applied_steps.append("numeric_cleaning")

        # 3) Categorical-specific cleaning
        work_df = self._categorical_cleaner.clean(work_df, dtypes)
        report.applied_steps.append("categorical_cleaning")

        # 4) Feature engineering
        work_df = self._feature_engineer.apply(work_df, dtypes)
        report.applied_steps.append("feature_engineering")

        # 5) Validation / warnings
        validation = self._validator.validate(work_df, dtypes)
        report.validation_report = validation
        report.applied_steps.append("validation")

        report.final_shape = work_df.shape
        return work_df, report
