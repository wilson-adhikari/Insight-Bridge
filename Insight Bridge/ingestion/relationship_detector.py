# ingestion/relationship_detector.py
from __future__ import annotations
from typing import Dict, List, Tuple
from sqlalchemy import create_engine, inspect


class RelationshipDetector:
    """
    Uses SQLAlchemy inspector to detect foreign-key relationships
    between multiple tables of the same database.
    """

    def __init__(self, conn_str: str) -> None:
        self._engine = create_engine(conn_str)

    def detect(self, table_names: List[str]) -> Dict[Tuple[str, str], List[str]]:
        """
        Returns mapping (parent_table, child_table) -> list of constrained columns.
        """
        insp = inspect(self._engine)
        rels: Dict[Tuple[str, str], List[str]] = {}

        for t in table_names:
            try:
                fks = insp.get_foreign_keys(t)
                for fk in fks:
                    parent = fk["referred_table"]
                    if parent in table_names:
                        cols = fk.get("constrained_columns", [])
                        key = (parent, t)
                        rels.setdefault(key, []).extend(cols)
            except Exception:
                continue  # Skip tables without FK info

        return rels