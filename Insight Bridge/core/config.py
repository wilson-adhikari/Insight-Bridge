# core/config.py
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CleaningThresholds:
    high_cardinality_ratio: float = 0.2
    imbalance_threshold: float = 0.9
    outlier_iqr_multiplier: float = 1.5


@dataclass
class AppConfig:
    cleaning: CleaningThresholds = field(default_factory=CleaningThresholds)
    # Per-user data dir: the cwd may be read-only (e.g. Program Files).
    models_dir: str = field(default_factory=lambda: str(Path.home() / ".insightbridge" / "models"))
    sessions_dir: str = field(default_factory=lambda: str(Path.home() / ".insightbridge" / "sessions"))
