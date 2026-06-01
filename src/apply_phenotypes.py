"""Executable phenotype examples for the synthetic linked resource."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def load_phenotype_definitions(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _persistent_school_absence(education: pd.DataFrame, definition: dict) -> pd.DataFrame:
    threshold = float(definition["logic"]["threshold"])
    minimum_terms = int(definition["logic"]["minimum_terms"])
    valid = education[
        education["linked_child_id"].notna()
        & education["attendance_rate"].notna()
        & education["attendance_rate"].between(0, 1)
    ].copy()
    valid["is_absent_term"] = valid["attendance_rate"] < threshold
    summary = (
        valid.groupby("linked_child_id")
        .agg(eligible_terms=("attendance_rate", "size"), qualifying_terms=("is_absent_term", "sum"))
        .reset_index()
    )
    summary["phenotype_flag"] = summary["qualifying_terms"] >= minimum_terms
    return summary


def _recurrent_hospital_admission(health: pd.DataFrame, definition: dict) -> pd.DataFrame:
    minimum_admissions = int(definition["logic"]["minimum_admissions"])
    interval_days = int(definition["logic"]["interval_days"])
    valid = health[health["linked_child_id"].notna() & health["admission_date"].notna()].copy()
    rows: list[dict] = []
    for child_id, group in valid.groupby("linked_child_id"):
        dates = group["admission_date"].sort_values().reset_index(drop=True)
        qualifies = False
        if len(dates) >= minimum_admissions:
            for start in range(len(dates)):
                end = start + minimum_admissions - 1
                if end < len(dates) and (dates.iloc[end] - dates.iloc[start]).days <= interval_days:
                    qualifies = True
                    break
        rows.append({"linked_child_id": child_id, "admission_count": int(len(dates)), "phenotype_flag": qualifies})
    return pd.DataFrame(rows)


def _chronic_condition_group(health: pd.DataFrame, definition: dict) -> pd.DataFrame:
    groups = set(definition["logic"]["diagnosis_groups"])
    valid = health[health["linked_child_id"].notna() & health["diagnosis_group"].notna()].copy()
    valid["qualifies"] = valid["diagnosis_group"].isin(groups)
    summary = (
        valid.groupby("linked_child_id")
        .agg(eligible_admissions=("diagnosis_group", "size"), qualifying_admissions=("qualifies", "sum"))
        .reset_index()
    )
    summary["phenotype_flag"] = summary["qualifying_admissions"] >= 1
    return summary


def apply_all_phenotypes(
    children: pd.DataFrame,
    health: pd.DataFrame,
    education: pd.DataFrame,
    definitions_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute configured phenotype examples and return child flags and prevalence."""

    definitions = load_phenotype_definitions(definitions_path)
    frames: list[pd.DataFrame] = []
    prevalence_rows: list[dict] = []
    total_children = len(children)

    for name, definition in definitions.items():
        if name == "persistent_school_absence":
            result = _persistent_school_absence(education, definition)
        elif name == "recurrent_hospital_admission":
            result = _recurrent_hospital_admission(health, definition)
        elif name == "chronic_condition_group":
            result = _chronic_condition_group(health, definition)
        else:
            raise ValueError(f"No executable implementation is registered for phenotype: {name}")

        result.insert(0, "phenotype", name)
        result.insert(1, "version", str(definition.get("version", "unknown")))
        frames.append(result)
        eligible_children = int(result["linked_child_id"].nunique())
        flagged_children = int(result.loc[result["phenotype_flag"], "linked_child_id"].nunique())
        prevalence_rows.append(
            {
                "phenotype": name,
                "version": str(definition.get("version", "unknown")),
                "description": str(definition.get("description", "")),
                "eligible_children": eligible_children,
                "flagged_children": flagged_children,
                "prevalence_among_eligible": round(flagged_children / eligible_children, 6) if eligible_children else 0.0,
                "coverage_of_spine": round(eligible_children / total_children, 6) if total_children else 0.0,
                "limitations": " | ".join(definition.get("limitations", [])),
            }
        )
    child_flags = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    return child_flags, pd.DataFrame(prevalence_rows)
