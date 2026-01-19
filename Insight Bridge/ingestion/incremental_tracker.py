# ingestion/incremental_tracker.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional
import json


@dataclass
class IncrementalSignature:
    source_id: str
    last_row_id: Optional[int] = None
    last_timestamp: Optional[str] = None


class IncrementalTracker:
    """Persists incremental signatures in a small JSON file."""

    def __init__(self, path: str | Path = "incremental_state.json") -> None:
        self.path = Path(path)
        self.signatures: Dict[str, IncrementalSignature] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.signatures = {}
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.signatures = {k: IncrementalSignature(**v) for k, v in data.items()}
        except Exception:
            self.signatures = {}

    def _save(self) -> None:
        data = {k: asdict(v) for k, v in self.signatures.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, source_id: str) -> Optional[IncrementalSignature]:
        return self.signatures.get(source_id)

    def update(self, sig: IncrementalSignature) -> None:
        self.signatures[sig.source_id] = sig
        self._save()