# core/state.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import pandas as pd

from .schemas import TableSchema, ModelMetadataSchema


@dataclass
class AppState:
    def __init__(self) -> None:
        self.tables: dict[str, pd.DataFrame] = {}
        self.active_table_name: str | None = None
        self.schemas: dict[str, Any] = {}

        # ML state
        self.last_ml_key: str | None = None
        self.last_ml_task: str | None = None  # "regression" | "classification" | "clustering"
        self.last_ml_num_cols: list[str] = []
        self.last_ml_cat_cols: list[str] = []
        self.last_ml_target: str | None = None

    def active_df(self) -> pd.DataFrame | None:
        if self.active_table_name is None:
            return None
        return self.tables.get(self.active_table_name)

    def active_schema(self):
        if self.active_table_name is None:
            return None
        return self.schemas.get(self.active_table_name)


    def active_schema(self) -> Optional[TableSchema]:
        if self.active_table_name and self.active_table_name in self.schemas:
            return self.schemas[self.active_table_name]
        return None
