# ingestion/sql_loader.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Dict
import pandas as pd
from sqlalchemy import create_engine


@dataclass
class SQLConnectionConfig:
    conn_str: str


class SQLLoader:
    def __init__(self, conn_str: str) -> None:
        self.config = SQLConnectionConfig(conn_str=conn_str)
        self._engine = create_engine(conn_str)

    @property
    def engine(self):
        return self._engine

    def load_table(self, table_name: str, **kwargs: Any) -> pd.DataFrame:
        return pd.read_sql_table(table_name, con=self._engine, **kwargs)

    def load_query(self, query: str, **kwargs: Any) -> pd.DataFrame:
        return pd.read_sql(query, con=self._engine, **kwargs)

    def load_tables(self, table_names: List[str]) -> Dict[str, pd.DataFrame]:
        return {name: self.load_table(name) for name in table_names}