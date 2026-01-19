# ingestion/excel_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd


class ExcelLoader:
    def load(self, path: str | Path, sheet_name: str | int | None = 0, **kwargs: Any) -> pd.DataFrame:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", **kwargs)