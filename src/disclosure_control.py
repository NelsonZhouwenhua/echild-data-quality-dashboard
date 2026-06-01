"""Illustrative public-output disclosure controls for synthetic aggregates.

These rules are for a portfolio demonstration only. They do not reproduce
Office for National Statistics Secure Research Service output checking.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


DEFAULT_THRESHOLD = 10


def load_disclosure_rules(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("public_output_rules", {})


def suppress_count(value: int | float, threshold: int = DEFAULT_THRESHOLD) -> str | int:
    """Suppress non-zero small counts while preserving zero counts."""

    if pd.isna(value):
        return ""
    numeric = int(value)
    if 0 < numeric < threshold:
        return f"<{threshold}"
    return numeric


def suppress_small_counts(
    frame: pd.DataFrame,
    count_columns: Iterable[str],
    threshold: int = DEFAULT_THRESHOLD,
) -> pd.DataFrame:
    """Return a display copy with selected count columns suppressed."""

    display = frame.copy()
    for column in count_columns:
        if column in display.columns:
            display[column] = display[column].map(lambda value: suppress_count(value, threshold))
    return display


def public_mode_banner(threshold: int = DEFAULT_THRESHOLD) -> str:
    return (
        "Public portfolio mode: only aggregate outputs are displayed. "
        f"Non-zero cells below {threshold} are suppressed using an illustrative rule. "
        "This does not claim to reproduce ONS SRS output-checking rules."
    )
