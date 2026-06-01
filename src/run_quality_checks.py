"""Reusable data-quality checks for synthetic linked administrative records."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


def _issue(source: str, record_id: str, check: str, severity: str, detail: str) -> dict:
    return {
        "source": source,
        "source_record_id": record_id,
        "check_name": check,
        "severity": severity,
        "detail": detail,
    }


def detect_duplicate_record_ids(df: pd.DataFrame, source: str) -> list[dict]:
    duplicated = df[df["source_record_id"].duplicated(keep=False)]["source_record_id"].astype(str).unique()
    return [
        _issue(source, record_id, "duplicate_source_record_id", "warning", "Source record identifier occurs more than once")
        for record_id in duplicated
    ]


def check_health(health: pd.DataFrame, children: pd.DataFrame) -> list[dict]:
    issues: list[dict] = []
    issues.extend(detect_duplicate_record_ids(health, "health"))
    linked = health.merge(children[["child_id", "birth_date"]], left_on="linked_child_id", right_on="child_id", how="left")
    for row in linked[linked["admission_date"] < linked["birth_date"]].itertuples(index=False):
        issues.append(_issue("health", str(row.source_record_id), "admission_before_birth", "error", "Admission date is earlier than birth date"))
    for row in linked[linked["discharge_date"] < linked["admission_date"]].itertuples(index=False):
        issues.append(_issue("health", str(row.source_record_id), "discharge_before_admission", "error", "Discharge date is earlier than admission date"))
    return issues


def check_education(education: pd.DataFrame, children: pd.DataFrame) -> list[dict]:
    issues: list[dict] = []
    issues.extend(detect_duplicate_record_ids(education, "education"))
    invalid = education[education["attendance_rate"].notna() & ~education["attendance_rate"].between(0, 1)]
    for row in invalid.itertuples(index=False):
        issues.append(_issue("education", str(row.source_record_id), "attendance_out_of_range", "error", "Attendance rate is outside [0, 1]"))
    linked = education.merge(children[["child_id", "birth_date"]], left_on="linked_child_id", right_on="child_id", how="left")
    linked["age"] = linked["academic_year"] - linked["birth_date"].dt.year
    inconsistent = linked[
        ((linked["age"].between(5, 10)) & (linked["school_stage"] != "Primary"))
        | ((linked["age"].between(11, 15)) & (linked["school_stage"] != "Secondary"))
        | ((linked["age"] >= 16) & (linked["school_stage"] != "Post-16"))
    ]
    for row in inconsistent.itertuples(index=False):
        issues.append(_issue("education", str(row.source_record_id), "school_stage_age_inconsistency", "warning", "School stage is inconsistent with age"))
    return issues


def check_social_care(social: pd.DataFrame, children: pd.DataFrame) -> list[dict]:
    issues: list[dict] = []
    issues.extend(detect_duplicate_record_ids(social, "social_care"))
    linked = social.merge(children[["child_id", "birth_date"]], left_on="linked_child_id", right_on="child_id", how="left")
    for row in linked[linked["referral_date"] < linked["birth_date"]].itertuples(index=False):
        issues.append(_issue("social_care", str(row.source_record_id), "referral_before_birth", "error", "Referral date is earlier than birth date"))
    return issues


def variable_metrics(source: str, df: pd.DataFrame, columns: list[str]) -> list[dict]:
    rows: list[dict] = []
    for column in columns:
        n_records = len(df)
        n_missing = int(df[column].isna().sum())
        missing_rate = float(n_missing / n_records) if n_records else 0.0
        rows.append(
            {
                "source": source,
                "variable_name": column,
                "n_records": n_records,
                "n_missing": n_missing,
                "missing_rate": round(missing_rate, 6),
                "completeness_rate": round(1.0 - missing_rate, 6),
            }
        )
    return rows


def run_all_quality_checks(
    children: pd.DataFrame,
    health: pd.DataFrame,
    education: pd.DataFrame,
    social: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    issue_rows: list[dict] = []
    issue_rows.extend(check_health(health, children))
    issue_rows.extend(check_education(education, children))
    issue_rows.extend(check_social_care(social, children))

    metric_rows: list[dict] = []
    metric_rows.extend(variable_metrics("children", children, ["birth_date", "sex", "region", "deprivation_quintile", "ethnicity_group"]))
    metric_rows.extend(variable_metrics("health", health, ["admission_date", "discharge_date", "diagnosis_group", "admission_type", "linked_child_id"]))
    metric_rows.extend(variable_metrics("education", education, ["academic_year", "term", "school_stage", "attendance_rate", "sen_support", "linked_child_id"]))
    metric_rows.extend(variable_metrics("social_care", social, ["referral_date", "event_type", "reason_group", "assessment_outcome", "linked_child_id"]))
    return pd.DataFrame(metric_rows), pd.DataFrame(issue_rows)


def build_rule_summary(
    issues: pd.DataFrame,
    education: pd.DataFrame,
    social: pd.DataFrame,
    rules_path: Path,
) -> pd.DataFrame:
    """Join rule metadata to record-level flags and metric-level warnings."""

    with rules_path.open("r", encoding="utf-8") as handle:
        rules = pd.DataFrame(yaml.safe_load(handle) or [])
    issue_counts = issues.groupby(["source", "check_name"], dropna=False).size().reset_index(name="flagged_records")
    rules = rules.merge(issue_counts, on=["source", "check_name"], how="left")

    attendance_2020 = education.loc[education["academic_year"].eq(2020), "attendance_rate"]
    attendance_other = education.loc[~education["academic_year"].eq(2020), "attendance_rate"]
    attendance_shift = float(attendance_2020.isna().mean() - attendance_other.isna().mean())
    social_by_region = social.groupby("local_authority_region")["assessment_outcome"].apply(lambda series: series.isna().mean())
    social_shift = float(social_by_region.max() - social_by_region.min()) if not social_by_region.empty else 0.0

    metric_counts = {
        "attendance_missingness_shift_2020": int(attendance_shift > 0.10),
        "assessment_outcome_regional_missingness_shift": int(social_shift > 0.10),
    }
    for index, row in rules.iterrows():
        if row["check_name"] in metric_counts:
            rules.loc[index, "flagged_records"] = metric_counts[row["check_name"]]
        if row["check_name"] == "duplicate_source_record_id" and row["source"] == "all":
            rules.loc[index, "flagged_records"] = int((issues["check_name"] == "duplicate_source_record_id").sum())

    rules["flagged_records"] = rules["flagged_records"].fillna(0).astype(int)
    rules["status"] = rules["flagged_records"].map(lambda count: "Review" if count > 0 else "Passed")
    return rules[["rule_id", "source", "category", "severity", "check_name", "flagged_records", "status", "recommended_action"]]
