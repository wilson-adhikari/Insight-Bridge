# utils/theming.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Theme:
    primary_color: str = "#2E86AB"
    accent_color: str = "#F6A01A"
    background_color: str = "#FFFFFF"
    warning_color: str = "#E74C3C"


DEFAULT_THEME = Theme()
