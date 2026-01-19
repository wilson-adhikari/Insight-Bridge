# ml/explainability.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance


@dataclass
class FeatureImportanceResult:
    feature_names: List[str]
    importances: np.ndarray


def tree_feature_importance(model, feature_names: List[str]) -> FeatureImportanceResult:
    """Works for RandomForestClassifier/Regressor."""
    if not hasattr(model, "feature_importances_"):
        raise ValueError("Model has no feature_importances_ attribute.")
    imps = model.feature_importances_
    return FeatureImportanceResult(feature_names=feature_names, importances=imps)


def permutation_importance_simple(
    fitted_pipeline,
    X_val: pd.DataFrame,
    y_val,
    n_repeats: int = 10,
) -> FeatureImportanceResult:
    """Model-agnostic importance using sklearn permutation_importance."""
    # assume last step is 'model', and we can call pipeline.predict
    result = permutation_importance(fitted_pipeline, X_val, y_val, n_repeats=n_repeats, random_state=42)
    importances_mean = result.importances_mean
    return FeatureImportanceResult(feature_names=list(X_val.columns), importances=importances_mean)
