# ingestion/csv_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd


class CSVLoader:
    def load(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return self.csv_loader.load(path, **kwargs)
