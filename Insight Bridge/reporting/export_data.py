# reporting/export_data.py
from __future__ import annotations
from pathlib import Path
from typing import Dict
import pandas as pd


def export_cleaned_to_csv(df: pd.DataFrame, path: str | Path) -> None:
    df.to_csv(path, index=False)


def export_cleaned_to_excel(datasets: Dict[str, pd.DataFrame], path: str | Path) -> None:
    """
    datasets: sheet_name -> DataFrame
    Writes multiple sheets (raw, cleaned, ml_ready, etc.)[web:186][web:194][web:190]
    """
    with pd.ExcelWriter(path) as writer:
        for sheet_name, data in datasets.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)


def export_cleaned_to_sql(df: pd.DataFrame, table_name: str, conn_str: str, if_exists: str = "replace") -> None:
    from sqlalchemy import create_engine
    engine = create_engine(conn_str)
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
