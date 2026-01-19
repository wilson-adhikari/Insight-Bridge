# core/schemas.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ColumnSchema:
    name: str
    logical_type: str                   # "numeric", "categorical", "datetime", "boolean", "ordinal"
    inferred_type: str
    user_override: Optional[str] = None


@dataclass
class TableSchema:
    name: str
    columns: Dict[str, ColumnSchema] = field(default_factory=dict)


@dataclass
class ModelMetadataSchema:
    key: str
    kind: str
    model_name: str
    input_columns: List[str]
    target_columns: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)
