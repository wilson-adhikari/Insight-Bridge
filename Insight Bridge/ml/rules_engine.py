# ml/rules_engine.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Any, List

import pandas as pd


Op = Literal[">", ">=", "<", "<=", "==", "!="]


@dataclass
class Rule:
    source_col: str      # e.g. "y_pred" or "cluster_label"
    op: Op
    threshold: Any       # numeric or category
    target_col: str      # e.g. "alert", "risk_flag"
    target_value: Any    # e.g. True, "High risk"


class RulesEngine:
    """Applies user-defined decision rules to a DataFrame."""

    def apply_rules(self, df: pd.DataFrame, rules: List[Rule]) -> pd.DataFrame:
        result = df.copy()
        for rule in rules:
            if rule.target_col not in result.columns:
                result[rule.target_col] = False if isinstance(rule.target_value, bool) else None
            src = result[rule.source_col]

            if rule.op == ">":
                mask = src > rule.threshold
            elif rule.op == ">=":
                mask = src >= rule.threshold
            elif rule.op == "<":
                mask = src < rule.threshold
            elif rule.op == "<=":
                mask = src <= rule.threshold
            elif rule.op == "==":
                mask = src == rule.threshold
            elif rule.op == "!=":
                mask = src != rule.threshold
            else:
                continue

            result.loc[mask, rule.target_col] = rule.target_value
        return result
