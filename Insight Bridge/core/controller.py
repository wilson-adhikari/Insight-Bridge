# core/controller.py
from __future__ import annotations

from typing import List, Optional, Dict, Any
import traceback

import pandas as pd

from ingestion.data_manager import DataManager
from ingestion.type_inference import TypeInference

from cleaning.preprocessor import Preprocessor, CleaningConfig, CleaningReport
from cleaning.type_casting import TypeCaster, TypeCastingConfig

from analysis.numeric_analysis import analyze_numeric, NumericAnalysisResult
from analysis.categorical_analysis import freq_table
from analysis.correlation import correlation_matrix
from analysis.relationship_explorer import scan_numeric_vs_categorical, NumericCategoricalRelation

from ml.ml_manager import MLManager, TrainedModelInfo

from reporting.export_data import (
    export_cleaned_to_csv,
    export_cleaned_to_excel,
)
from reporting.report_builder import ReportContent, SectionText, build_pdf_report
from reporting.session_manager import SessionManager, SessionState

from core.state import AppState
from core.schemas import ColumnSchema, TableSchema
from core.config import AppConfig


class Controller:
    """Main orchestrator between backend modules and UI."""

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.config = config or AppConfig()
        self.state = AppState()
        self.data_manager = DataManager()
        self.type_infer = TypeInference()
        self.type_caster = TypeCaster(TypeCastingConfig())
        self.preprocessor = Preprocessor()
        self.ml_manager = MLManager()
        self.session_manager = SessionManager(self.config.sessions_dir)

    # ---------- Data Loading (Robust & Safe) ----------
    def load_csv(self, name: str, path: str):
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
        df = None
        last_error = None
        for enc in encodings:
            try:
                df = pd.read_csv(
                    path,
                    encoding=enc,
                    low_memory=False,
                    on_bad_lines="skip",  # Skip malformed rows
                    dtype=str,  # Read everything as string first for safety
                )
                print(f"[Controller] CSV loaded successfully with encoding: {enc}")
                break
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                break

        if df is None:
            raise ValueError(f"Failed to read CSV (tried multiple encodings). Last error: {last_error}")

        self._post_load_processing(name, df)

    def load_excel(self, name: str, path: str):
        try:
            df = pd.read_excel(path, engine="openpyxl", dtype=str)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")
        self._post_load_processing(name, df)

    def load_sql_table(self, name: str, conn_str: str, table_name: str):
        try:
            df = pd.read_sql_table(table_name, conn_str)
        except Exception as e:
            raise ValueError(f"Failed to load SQL table: {e}")
        self._post_load_processing(name, df)

    def load_sql_tables(self, conn_str: str, table_names: List[str]):
        for table_name in table_names:
            df = pd.read_sql_table(table_name, conn_str)
            self._post_load_processing(table_name, df)

    def _post_load_processing(self, name: str, df: pd.DataFrame):
        """Common processing after any load: store raw, infer schema, cast types."""
        if df.empty:
            raise ValueError("Loaded DataFrame is empty.")

        # Store raw (string) version as fallback
        self.state.tables[name] = df.copy()

        # Infer logical types
        schema = self.type_infer.infer(df)
        self.state.schemas[name] = schema

        # Apply safe type casting
        logical_dtypes = {c.name: c.logical_type for c in schema.columns.values()}
        try:
            casted_df = self.type_caster.cast(df, logical_dtypes)
            self.state.tables[name] = casted_df
            print(f"[Controller] Type casting successful for {name}")
        except Exception as e:
            print(f"[Controller] Type casting failed (using raw string DF): {e}")
            traceback.print_exc()
            # Keep raw string DF if casting fails

        self.state.active_table_name = name

    # ---------- Cleaning ----------
    def clean_active(self, cfg: CleaningConfig) -> tuple[Optional[pd.DataFrame], CleaningReport]:
        df = self.state.active_df()
        schema = self.state.active_schema()

        if df is None or schema is None:
            return None, CleaningReport(initial_shape=(0, 0), final_shape=(0, 0), applied_steps=[])

        logical_dtypes = {c.name: c.logical_type for c in schema.columns.values()}

        # Update preprocessor config from UI cfg, then call clean()
        self.preprocessor.config = cfg
        cleaned_df, report = self.preprocessor.clean(df, logical_dtypes)  # <- was .apply

        # Update active table with cleaned version
        if self.state.active_table_name:
            self.state.tables[self.state.active_table_name] = cleaned_df

        return cleaned_df, report


    # ---------- Analysis ----------
    def numeric_analysis(self) -> Optional[NumericAnalysisResult]:
        df = self.state.active_df()
        schema = self.state.active_schema()
        if df is None or schema is None:
            return None

        numeric_cols = [c.name for c in schema.columns.values() if c.logical_type == "numeric"]
        if not numeric_cols:
            return None

        return analyze_numeric(df, numeric_cols)

    def categorical_analysis(self, col: str) -> Optional[pd.DataFrame]:
        df = self.state.active_df()
        if df is None or col not in df.columns:
            return None
        return freq_table(df, col)

    def relationship_hints(self) -> List[NumericCategoricalRelation]:
        df = self.state.active_df()
        schema = self.state.active_schema()
        if df is None or schema is None:
            return []

        numeric_cols = [c.name for c in schema.columns.values() if c.logical_type == "numeric"]
        cat_cols = [c.name for c in schema.columns.values() if c.logical_type == "categorical"]

        return scan_numeric_vs_categorical(df, numeric_cols, cat_cols)

    # ---------- ML ----------
    def train_regression_with_columns(
        self,
        model_name: str,
        target: str,
        num_cols: list[str],
        cat_cols: list[str],
    ):
        df = self.state.active_df()
        if df is None:
            raise ValueError("No active data.")
        info = self.ml_manager.train_regression(
            model_name=model_name,
            df=df,
            numeric_cols=num_cols,
            categorical_cols=cat_cols,
            target_col=target,
        )
        # remember in state
        self.state.last_ml_key = info.key
        self.state.last_ml_task = "regression"
        self.state.last_ml_num_cols = num_cols
        self.state.last_ml_cat_cols = cat_cols
        self.state.last_ml_target = target
        return info

    def train_classification_with_columns(
        self,
        model_name: str,
        target: str,
        num_cols: list[str],
        cat_cols: list[str],
    ):
        df = self.state.active_df()
        if df is None:
            raise ValueError("No active data.")
        info = self.ml_manager.train_classification(
            model_name=model_name,
            df=df,
            numeric_cols=num_cols,
            categorical_cols=cat_cols,
            target_col=target,
        )
        self.state.last_ml_key = info.key
        self.state.last_ml_task = "classification"
        self.state.last_ml_num_cols = num_cols
        self.state.last_ml_cat_cols = cat_cols
        self.state.last_ml_target = target
        return info

    def train_clustering_with_columns(
        self,
        model_name: str,
        num_cols: list[str],
        cat_cols: list[str],  # cat_cols unused but kept for same signature
    ):
        df = self.state.active_df()
        if df is None:
            raise ValueError("No active data.")
        info, labels = self.ml_manager.train_clustering(
            model_name=model_name,
            df=df,
            numeric_cols=num_cols,
        )
        self.state.last_ml_key = info.key
        self.state.last_ml_task = "clustering"
        self.state.last_ml_num_cols = num_cols
        self.state.last_ml_cat_cols = []
        self.state.last_ml_target = None
        return info, labels

    # ---------- Export ----------
    def export_active_to_csv(self, path: str):
        df = self.state.active_df()
        if df is not None and self.state.active_table_name:
            export_cleaned_to_csv(
                {self.state.active_table_name: df},
                path,
            )

    def export_active_to_excel(self, path: str):
        df = self.state.active_df()
        if df is not None and self.state.active_table_name:
            export_cleaned_to_excel(
                {self.state.active_table_name: df},
                path,
            )

    # ---------- Reporting ----------
    def build_basic_report(self, path: str, title: str = "Analysis Report"):
        df = self.state.active_df()
        if df is None:
            return

        sections = [
            SectionText(title="Dataset Overview", body=f"Rows: {len(df):,}\nColumns: {df.shape[1]}"),
            SectionText(title="Column Types", body=str(df.dtypes.to_string())),
        ]

        # Add simple stats if possible
        numeric_result = self.numeric_analysis()
        if numeric_result:
            stats_text = "\n\n".join([
                f"{col}:\n{summary}"
                for col, summary in numeric_result.summaries.items()
            ])
            sections.append(SectionText(title="Numeric Summary", body=stats_text))

        content = ReportContent(title=title, sections=sections, figures=[])
        build_pdf_report(content, path)

    # ---------- Session Management ----------
    def save_session(self, name: str):
        state = SessionState(
            active_dataset_name=self.state.active_table_name,
            datasets=list(self.state.tables.keys()),
            models={k: v.dict() for k, v in self.state.models.items()},  # assuming ModelMetadataSchema has .dict()
            extra={},
        )
        self.session_manager.save(name, state)

    def load_session(self, name: str):
        loaded = self.session_manager.load(name)
        if loaded:
            # In a full implementation: reload tables/models from disk paths stored in loaded
            # For now: just set active name
            if loaded.active_dataset_name in self.state.tables:
                self.state.active_table_name = loaded.active_dataset_name