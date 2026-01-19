# reporting/session_manager.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional
import json


@dataclass
class SessionState:
    """Lightweight snapshot of analysis session (refs to data/model ids, not raw DataFrames)."""
    active_dataset_name: Optional[str]
    datasets: Dict[str, str]       # logical_name -> file path or table id
    models: Dict[str, str]         # model_key -> description or file id
    extra: Dict[str, Any]


class SessionManager:
    def __init__(self, base_dir: str | Path = "sessions") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        return self.base_dir / f"{name}.session.json"

    def save(self, name: str, state: SessionState) -> None:
        path = self._path_for(name)
        data = asdict(state)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, name: str) -> SessionState:
        path = self._path_for(name)
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data)
