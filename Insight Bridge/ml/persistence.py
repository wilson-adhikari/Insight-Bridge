# ml/persistence.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional

import json
import joblib  # optimized for sklearn models & numpy arrays[web:140][web:158][web:155]


@dataclass
class ModelMetadata:
    key: str                  # internal id, e.g. "clf_rf_target"
    kind: str                 # "regression" | "classification" | "clustering"
    model_name: str           # "linear", "rf", "logistic", "kmeans", etc.
    version: str = "1.0"
    created_at: Optional[str] = None       # ISO timestamp (optional, set by caller)
    input_columns: Optional[list[str]] = None
    target_columns: Optional[list[str]] = None
    extra: Dict[str, Any] = None          # metrics, notes, anything serializable


class ModelPersistence:
    """Handles saving and loading trained models with sidecar JSON metadata."""

    def __init__(self, base_dir: str | Path = "models") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _paths_for_key(self, key: str) -> tuple[Path, Path]:
        """Return (model_path, metadata_path) for a given key."""
        model_path = self.base_dir / f"{key}.joblib"
        meta_path = self.base_dir / f"{key}.metadata.json"
        return model_path, meta_path

    def save(
        self,
        key: str,
        model: Any,
        metadata: ModelMetadata,
        compress: int = 3,
    ) -> None:
        """
        Persist model + metadata to disk.

        key: unique identifier for the model (used as filename).
        model: sklearn Pipeline or estimator.
        metadata: ModelMetadata describing inputs/outputs, metrics, etc.
        """
        model_path, meta_path = self._paths_for_key(key)

        # save model
        joblib.dump(model, model_path, compress=compress)  # single file joblib dump[web:142][web:147]

        # save metadata
        meta_dict = asdict(metadata)
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

    def load(self, key: str) -> tuple[Any, ModelMetadata]:
        """
        Load model + metadata by key.

        Returns
        -------
        model, metadata
        """
        model_path, meta_path = self._paths_for_key(key)
        if not model_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Model or metadata for key '{key}' not found in {self.base_dir}")

        model = joblib.load(model_path)

        with meta_path.open("r", encoding="utf-8") as f:
            meta_dict = json.load(f)
        metadata = ModelMetadata(**meta_dict)

        return model, metadata

    def list_models(self) -> list[str]:
        """Return all model keys (based on joblib files in the directory)."""
        keys: list[str] = []
        for p in self.base_dir.glob("*.joblib"):
            keys.append(p.stem)
        return keys

    def delete(self, key: str) -> None:
        """Remove model and metadata files for a given key."""
        model_path, meta_path = self._paths_for_key(key)
        if model_path.exists():
            model_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
