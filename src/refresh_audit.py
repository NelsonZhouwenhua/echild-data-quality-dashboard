"""Versioned release manifest comparison for the synthetic resource."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def load_release(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def compare_releases(previous_path: Path, current_path: Path) -> pd.DataFrame:
    previous = load_release(previous_path)
    current = load_release(current_path)
    sources = sorted(set(previous.get("sources", {})) | set(current.get("sources", {})))
    rows: list[dict] = []
    for source in sources:
        old = previous.get("sources", {}).get(source, {})
        new = current.get("sources", {}).get(source, {})
        old_modules = set(old.get("modules", []))
        new_modules = set(new.get("modules", []))
        old_years = f"{old.get('available_from', '-')}-{old.get('available_to', '-')}"
        new_years = f"{new.get('available_from', '-')}-{new.get('available_to', '-')}"
        changes: list[str] = []
        if old_years != new_years:
            changes.append(f"coverage {old_years} -> {new_years}")
        added = sorted(new_modules - old_modules)
        removed = sorted(old_modules - new_modules)
        if added:
            changes.append("added modules: " + ", ".join(added))
        if removed:
            changes.append("removed modules: " + ", ".join(removed))
        if not changes:
            changes.append("no structural change")
        rows.append(
            {
                "source": source,
                "previous_release": previous.get("release_id", "unknown"),
                "current_release": current.get("release_id", "unknown"),
                "previous_coverage": old_years,
                "current_coverage": new_years,
                "previous_modules": ", ".join(sorted(old_modules)),
                "current_modules": ", ".join(sorted(new_modules)),
                "change": "; ".join(changes),
                "qa_status": new.get("qa_status", "Unknown"),
            }
        )
    return pd.DataFrame(rows)
