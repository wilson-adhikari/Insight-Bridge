# ingestion/data_manager.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
from sqlalchemy import create_engine

from .csv_loader import CSVLoader
from .excel_loader import ExcelLoader
from .sql_loader import SQLLoader
from .relationship_detector import RelationshipDetector
from .incremental_tracker import IncrementalTracker, IncrementalSignature


@dataclass
class JoinPreviewConfig:
    on: List[str] | str
    how: str = "inner"
    limit: int = 100


class DataManager:
    """High-level facade wrapping CSV/Excel/SQL + joins + incremental."""

    def __init__(self, incremental_state_file: str | Path = "incremental_state.json") -> None:
        self.csv_loader = CSVLoader()
        self.excel_loader = ExcelLoader()
        self.incremental_tracker = IncrementalTracker(incremental_state_file)

    # ---------------- File loaders ----------------
    def load_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return self.csv_loader.load(path, **kwargs)

    def load_excel(self, path: str | Path, sheet_name: str | int | None = 0, **kwargs: Any) -> pd.DataFrame:
        return self.excel_loader.load(path, sheet_name=sheet_name, **kwargs)

    # ---------------- SQL loaders ----------------
    def load_sql_table(self, conn_str: str, table_name: str, **kwargs: Any) -> pd.DataFrame:
        loader = SQLLoader(conn_str)
        return loader.load_table(table_name, **kwargs)

    def load_sql_tables(self, conn_str: str, table_names: List[str]) -> Dict[str, pd.DataFrame]:
        loader = SQLLoader(conn_str)
        return loader.load_tables(table_names)

    def detect_relationships(self, conn_str: str, table_names: List[str]) -> Dict[Tuple[str, str], List[str]]:
        detector = RelationshipDetector(conn_str)
        return detector.detect(table_names)

    # ---------------- Join preview ----------------
    def preview_join(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        config: JoinPreviewConfig,
    ) -> pd.DataFrame:
        how = config.how.lower()
        if how not in {"left", "right", "outer", "inner", "cross"}:
            how = "inner"

        merged = pd.merge(left, right, on=config.on, how=how, suffixes=("_left", "_right"))
        return merged.head(config.limit)

    # ---------------- Incremental SQL ----------------
    def load_sql_incremental(
        self,
        conn_str: str,
        table_name: str,
        key_column: str,
        source_id: Optional[str] = None,
    ) -> pd.DataFrame:
        engine = create_engine(conn_str)
        sid = source_id or f"{conn_str}|{table_name}|{key_column}"
        sig = self.incremental_tracker.get(sid)

        if sig is None or sig.last_row_id is None:
            query = f"SELECT * FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name} WHERE {key_column} > {sig.last_row_id}"

        df = pd.read_sql(query, con=engine)

        if not df.empty and key_column in df.columns:
            try:
                max_id = int(df[key_column].max())
                self.incremental_tracker.update(
                    IncrementalSignature(source_id=sid, last_row_id=max_id)
                )
            except (ValueError, TypeError):
                pass  # key_column not integer-like → no incremental tracking

        return df