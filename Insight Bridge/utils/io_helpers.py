# utils/io_helpers.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import json


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
