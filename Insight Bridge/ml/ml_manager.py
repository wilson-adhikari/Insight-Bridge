# ml/ml_manager.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from .pipelines import (
    regression_pipeline,
    classification_pipeline,
    clustering_pipeline,
)
from .evaluation import (
    regression_metrics,
    classification_metrics,
    clustering_metrics,
    RegressionMetrics,
    ClassificationMetrics,
    ClusteringMetrics,
)
from .explainability import (
    tree_feature_importance,
    permutation_importance_simple,
    FeatureImportanceResult,
)
from .rules_engine import RulesEngine, Rule
from .persistence import ModelPersistence, ModelMetadata


@dataclass
class TrainedModelInfo:
    key: str                      # unique key inside manager
    kind: str                     # "regression" | "classification" | "clustering"
    model_name: str               # "linear", "rf", "logistic", "kmeans", "dbscan"
    target_col: Optional[str]     # None for clustering
    metrics: Any                  # RegressionMetrics / ClassificationMetrics / ClusteringMetrics
    feature_importance: Optional[FeatureImportanceResult] = None
    persisted: bool = False       # whether saved to disk already


class MLManager:
    """High-level ML orchestrator used by controller/UI.

    Handles:
      - Regression, classification, clustering
      - Mixed numeric + categorical features
      - Metrics, basic explainability, optional persistence
    """

    def __init__(self, models_dir: str = "models") -> None:
        self.models: Dict[str, TrainedModelInfo] = {}
        self._pipelines: Dict[str, Any] = {}      # key -> sklearn Pipeline
        self.rules_engine = RulesEngine()
        self.persistence = ModelPersistence(base_dir=models_dir)

    # ------------------------------------------------------------------
    # Regression
    # ------------------------------------------------------------------
    def train_regression(
        self,
        model_name: str,                    # "linear" or "rf"
        df: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
        target_col: str,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> TrainedModelInfo:
        X = df[numeric_cols + categorical_cols]
        y = df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )  # standard train/test split[web:170][web:164]

        pipe = regression_pipeline(
            model=model_name,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
        )
        pipe.fit(X_train, y_train)

        y_pred = pipe.predict(X_test)
        met: RegressionMetrics = regression_metrics(y_test, y_pred)

        # Feature importance for RandomForestRegressor only (tree-based)
        fi: Optional[FeatureImportanceResult] = None
        if model_name == "rf":
            # feature names after ColumnTransformer are not trivial;
            # for now keep placeholder importance from underlying model
            rf = pipe.named_steps["model"]
            importances = getattr(rf, "feature_importances_", None)
            if importances is not None:
                # no easy names; just index-based
                fi = FeatureImportanceResult(
                    feature_names=[f"f_{i}" for i in range(len(importances))],
                    importances=importances,
                )

        key = f"reg_{model_name}_{target_col}"
        info = TrainedModelInfo(
            key=key,
            kind="regression",
            model_name=model_name,
            target_col=target_col,
            metrics=met,
            feature_importance=fi,
        )

        self.models[key] = info
        self._pipelines[key] = pipe
        return info

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    def train_classification(
        self,
        model_name: str,                    # "logistic" or "rf"
        df: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
        target_col: str,
        test_size: float = 0.2,
        random_state: int = 42,
        stratify: bool = True,
    ) -> TrainedModelInfo:
        X = df[numeric_cols + categorical_cols]
        y = df[target_col]

        stratify_arg = y if stratify else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_arg,
        )  # keeps class balance when desired[web:167][web:173]

        pipe = classification_pipeline(
            model=model_name,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
        )
        pipe.fit(X_train, y_train)

        y_pred = pipe.predict(X_test)
        # probability output if available (for ROC AUC)
        y_proba = pipe.predict_proba(X_test) if hasattr(pipe, "predict_proba") else None  # [web:160][web:172][web:169]
        met: ClassificationMetrics = classification_metrics(y_test, y_pred, y_proba=y_proba)

        fi: Optional[FeatureImportanceResult] = None
        if model_name == "rf":
            rf = pipe.named_steps["model"]
            importances = getattr(rf, "feature_importances_", None)
            if importances is not None:
                fi = FeatureImportanceResult(
                    feature_names=[f"f_{i}" for i in range(len(importances))],
                    importances=importances,
                )

        key = f"clf_{model_name}_{target_col}"
        info = TrainedModelInfo(
            key=key,
            kind="classification",
            model_name=model_name,
            target_col=target_col,
            metrics=met,
            feature_importance=fi,
        )

        self.models[key] = info
        self._pipelines[key] = pipe
        return info

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------
    def train_clustering(
        self,
        model_name: str,                # "kmeans" or "dbscan"
        df: pd.DataFrame,
        numeric_cols: List[str],
    ) -> Tuple[TrainedModelInfo, pd.Series]:
        X = df[numeric_cols]

        pipe = clustering_pipeline(
            model=model_name,
            numeric_cols=numeric_cols,
        )
        labels = pipe.fit_predict(X)

        met: ClusteringMetrics = clustering_metrics(X, labels)  # includes silhouette where valid[web:177][web:165][web:171]

        key = f"clu_{model_name}"
        info = TrainedModelInfo(
            key=key,
            kind="clustering",
            model_name=model_name,
            target_col=None,
            metrics=met,
            feature_importance=None,
        )

        self.models[key] = info
        self._pipelines[key] = pipe

        label_series = pd.Series(labels, index=df.index, name="cluster_label")
        return info, label_series

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        key: str,
        df_new: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
    ) -> pd.Series:
        """Predict using a previously trained model."""
        if key not in self._pipelines:
            raise KeyError(f"Model key '{key}' not found in MLManager.")
        pipe = self._pipelines[key]

        X_new = df_new[numeric_cols + categorical_cols]
        preds = pipe.predict(X_new)
        return pd.Series(preds, index=df_new.index, name="prediction")

    def predict_proba(
        self,
        key: str,
        df_new: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
    ) -> Optional[pd.DataFrame]:
        """Return class probabilities for classification models (if available)."""
        if key not in self._pipelines:
            raise KeyError(f"Model key '{key}' not found in MLManager.")
        pipe = self._pipelines[key]

        if not hasattr(pipe, "predict_proba"):
            return None

        X_new = df_new[numeric_cols + categorical_cols]
        proba = pipe.predict_proba(X_new)  # probability matrix[web:160][web:162]
        classes = pipe.named_steps["model"].classes_
        return pd.DataFrame(proba, index=df_new.index, columns=[f"class_{c}" for c in classes])

    # ------------------------------------------------------------------
    # Explainability (optional call from GUI)
    # ------------------------------------------------------------------
    def compute_permutation_importance(
        self,
        key: str,
        X_val: pd.DataFrame,
        y_val,
        n_repeats: int = 10,
    ) -> FeatureImportanceResult:
        if key not in self._pipelines:
            raise KeyError(f"Model key '{key}' not found in MLManager.")
        pipe = self._pipelines[key]
        fi = permutation_importance_simple(pipe, X_val, y_val, n_repeats=n_repeats)
        # store back into model info
        info = self.models[key]
        info.feature_importance = fi
        self.models[key] = info
        return fi

    # ------------------------------------------------------------------
    # Rules / decision engine
    # ------------------------------------------------------------------
    def apply_rules(self, df_with_preds: pd.DataFrame, rules: List[Rule]) -> pd.DataFrame:
        return self.rules_engine.apply_rules(df_with_preds, rules)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_model(
        self,
        key: str,
        input_columns: List[str],
        target_columns: Optional[List[str]] = None,
        created_at: Optional[str] = None,
    ) -> None:
        """Save a trained pipeline + metadata to disk."""
        if key not in self._pipelines or key not in self.models:
            raise KeyError(f"Model key '{key}' not found in MLManager.")

        pipe = self._pipelines[key]
        info = self.models[key]

        meta = ModelMetadata(
            key=key,
            kind=info.kind,
            model_name=info.model_name,
            version="1.0",
            created_at=created_at,
            input_columns=input_columns,
            target_columns=target_columns,
            extra={"metrics": getattr(info.metrics, "__dict__", str(info.metrics))},
        )
        self.persistence.save(key, pipe, meta)
        info.persisted = True
        self.models[key] = info

    def load_model(self, key: str) -> TrainedModelInfo:
        """Load pipeline + metadata from disk into manager; returns TrainedModelInfo."""
        model, meta = self.persistence.load(key)
        self._pipelines[key] = model

        # reconstruct a minimal TrainedModelInfo (metrics will be whatever was stored in extra)
        metrics = meta.extra.get("metrics") if meta.extra else None
        info = TrainedModelInfo(
            key=key,
            kind=meta.kind,
            model_name=meta.model_name,
            target_col=(meta.target_columns[0] if meta.target_columns else None),
            metrics=metrics,
            feature_importance=None,
            persisted=True,
        )
        self.models[key] = info
        return info

    def list_saved_models(self) -> List[str]:
        """List all model keys persisted on disk."""
        return self.persistence.list_models()
