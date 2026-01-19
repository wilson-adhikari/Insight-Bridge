# core/config.py
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CleaningThresholds:
    high_cardinality_ratio: float = 0.2
    imbalance_threshold: float = 0.9
    outlier_iqr_multiplier: float = 1.5


@dataclass
class AppConfig:
    cleaning: CleaningThresholds = field(default_factory=CleaningThresholds)
    models_dir: str = "models"
    sessions_dir: str = "sessions"
