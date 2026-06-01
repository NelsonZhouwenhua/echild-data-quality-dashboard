"""Build linked analysis-ready tables and aggregate support outputs."""
from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3

import pandas as pd

from src.apply_phenotypes import apply_all_phenotypes
from src.linkage_evaluation import evaluate_linkage
from src.refresh_audit import compare_releases, load_release
from src.run_quality_checks import build_rule_summary, run_all_quality_checks


def _read_dates(path: Path, date_cols: list[str]) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=date_cols)


def _link_source(source_df: pd.DataFrame, linkage: pd.DataFrame, source: str) -> pd.DataFrame:
    link = linkage[(linkage["source"] == source) & (linkage["match_status"] == "matched")]
    return source_df.merge(
        link[["source_row_id", "linked_child_id", "linkage_confidence"]],
        on="source_row_id",
        how="left",
        validate="one_to_one",
    )


def linkage_summary(linkage: pd.DataFrame) -> pd.DataFrame:
    summary = linkage.groupby(["source", "match_status"]).size().unstack(fill_value=0)
    for status in ["matched", "unmatched", "ambiguous"]:
        if status not in summary.columns:
            summary[status] = 0
    summary["records"] = summary[["matched", "unmatched", "ambiguous"]].sum(axis=1)
    summary["linkage_rate"] = (summary["matched"] / summary["records"]).round(6)
    return summary.reset_index()[["source", "records", "matched", "unmatched", "ambiguous", "linkage_rate"]]


def build_metadata_catalogue() -> pd.DataFrame:
    rows = [
        ("children", "population_spine", "child_id", "Synthetic population-spine identifier", "string", 2008, 2018, "Synthetic identifier only", "Synthetic generator v2.0", "Do not export row-level identifiers"),
        ("children", "population_spine", "birth_date", "Synthetic date of birth", "date", 2008, 2018, "Month-level aggregation is safer for public reporting", "Synthetic generator v2.0", "Use grouped age or birth year in public outputs"),
        ("children", "population_spine", "region", "Region of residence", "category", 2008, 2018, "Synthetic geography", "Synthetic generator v2.0", "Report small cells with suppression"),
        ("children", "population_spine", "deprivation_quintile", "Area-level deprivation quintile", "integer", 2008, 2018, "Synthetic area-level measure", "Synthetic generator v2.0", "Compare linkage rates by quintile"),
        ("health", "admissions", "admission_date", "Hospital admission date", "date", 2016, 2025, "Some deliberately invalid temporal records", "Synthetic generator v2.0", "Check events before birth"),
        ("health", "admissions", "diagnosis_group", "Grouped primary diagnosis", "category", 2016, 2025, "Simplified synthetic categories", "Synthetic generator v2.0", "Do not interpret as a clinical code list"),
        ("health", "admissions", "admission_type", "Type of admission", "category", 2016, 2025, "Synthetic categories", "Synthetic generator v2.0", "Use for descriptive feasibility only"),
        ("education", "attendance", "academic_year", "Academic year", "integer", 2017, 2025, "Records start in 2017", "Synthetic generator v2.0", "Check outcome window"),
        ("education", "attendance", "attendance_rate", "Term-level attendance proportion", "float", 2017, 2025, "Completeness is deliberately lower in 2020", "Synthetic generator v2.0", "Do not treat missing attendance as absence"),
        ("education", "enrolment", "school_stage", "School stage", "category", 2017, 2025, "Some deliberate age-stage conflicts", "Synthetic generator v2.0", "Check stage consistency with age"),
        ("education", "sen_support", "sen_support", "Synthetic special educational needs support status", "category", 2017, 2025, "Synthetic categories", "Synthetic generator v2.0", "Report not-recorded values"),
        ("social_care", "referrals", "referral_date", "Referral or event date", "date", 2016, 2025, "Some deliberately invalid temporal records", "Synthetic generator v2.0", "Check events before birth"),
        ("social_care", "assessments", "assessment_outcome", "Outcome recorded after assessment", "category", 2016, 2025, "Completeness differs by region", "Synthetic generator v2.0", "Report regional missingness"),
        ("linkage", "linkage", "match_status", "Synthetic operational linkage result", "category", 2016, 2025, "matched, unmatched or ambiguous", "Synthetic linkage simulator v2.0", "Report coverage before downstream analysis"),
        ("linkage", "linkage", "linkage_confidence", "Synthetic linkage confidence score", "float", 2016, 2025, "Demonstration metric, not a calibrated probability", "Synthetic linkage simulator v2.0", "Use only for threshold sensitivity examples"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "source",
            "module",
            "variable_name",
            "description",
            "data_type",
            "available_from",
            "available_to",
            "known_caveat",
            "provenance",
            "recommended_use",
        ],
    )


def _release_log(root: Path) -> pd.DataFrame:
    release = load_release(root / "config" / "releases" / "release_2026_01.yml")
    rows = []
    for source, details in release.get("sources", {}).items():
        rows.append(
            {
                "release_id": release.get("release_id"),
                "refresh_date": release.get("refresh_date"),
                "source": source,
                "modules": ", ".join(details.get("modules", [])),
                "available_from": details.get("available_from"),
                "available_to": details.get("available_to"),
                "qa_status": details.get("qa_status"),
            }
        )
    return pd.DataFrame(rows)


def _data_source_trends(health: pd.DataFrame, education: pd.DataFrame, social: pd.DataFrame) -> pd.DataFrame:
    frames = []
    health_years = health.assign(year=health["admission_date"].dt.year).groupby("year").size().reset_index(name="records")
    health_years.insert(0, "source", "health")
    education_years = education.groupby("academic_year").size().reset_index(name="records").rename(columns={"academic_year": "year"})
    education_years.insert(0, "source", "education")
    social_years = social.assign(year=social["referral_date"].dt.year).groupby("year").size().reset_index(name="records")
    social_years.insert(0, "source", "social_care")
    frames.extend([health_years, education_years, social_years])
    return pd.concat(frames, ignore_index=True)


def _missingness_trends(education: pd.DataFrame, social: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    education_by_year = (
        education.groupby("academic_year")["attendance_rate"]
        .apply(lambda series: series.isna().mean())
        .reset_index(name="attendance_missing_rate")
    )
    social_by_region = (
        social.groupby("local_authority_region")["assessment_outcome"]
        .apply(lambda series: series.isna().mean())
        .reset_index(name="assessment_outcome_missing_rate")
    )
    return education_by_year, social_by_region


def _write(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _write_sqlite(processed: Path, tables: dict[str, pd.DataFrame]) -> None:
    db_path = processed / "synthetic_echild.db"
    temp_path = Path("/tmp/synthetic_echild_v2.db")
    if temp_path.exists():
        temp_path.unlink()
    with sqlite3.connect(temp_path) as connection:
        connection.execute("PRAGMA journal_mode=MEMORY")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA temp_store=MEMORY")
        for name, frame in tables.items():
            subset = frame
            if len(frame) > 30_000:
                subset = frame.sample(n=30_000, random_state=1)
            subset.to_sql(name, connection, if_exists="replace", index=False, chunksize=500, method="multi")
    shutil.copy2(temp_path, db_path)


def build_processed(repo_root: Path) -> None:
    raw = repo_root / "data" / "raw"
    internal = repo_root / "data" / "internal"
    processed = repo_root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    children = _read_dates(raw / "children.csv", ["birth_date"])
    health_raw = _read_dates(raw / "health_episodes.csv", ["admission_date", "discharge_date"])
    education_raw = pd.read_csv(raw / "education_records.csv")
    social_raw = _read_dates(raw / "social_care_events.csv", ["referral_date"])
    linkage = pd.read_csv(raw / "linkage_table.csv")
    truth = pd.read_csv(internal / "linkage_truth.csv")

    health = _link_source(health_raw, linkage, "health")
    education = _link_source(education_raw, linkage, "education")
    social = _link_source(social_raw, linkage, "social_care")

    metrics, issues = run_all_quality_checks(children, health, education, social)
    basic_linkage = linkage_summary(linkage)
    linkage_outputs = evaluate_linkage(linkage, truth, children)
    catalogue = build_metadata_catalogue()
    observed = metrics[["source", "variable_name", "missing_rate", "completeness_rate"]]
    catalogue = catalogue.merge(observed, on=["source", "variable_name"], how="left")

    phenotype_flags, phenotype_prevalence = apply_all_phenotypes(
        children,
        health,
        education,
        repo_root / "config" / "phenotypes.yml",
    )
    rule_summary = build_rule_summary(
        issues,
        education,
        social,
        repo_root / "config" / "quality_rules.yml",
    )
    release_diff = compare_releases(
        repo_root / "config" / "releases" / "release_2025_01.yml",
        repo_root / "config" / "releases" / "release_2026_01.yml",
    )
    refresh_log = _release_log(repo_root)
    source_trends = _data_source_trends(health, education, social)
    education_missingness, social_missingness = _missingness_trends(education, social)

    tables = {
        "children": children,
        "health_linked": health,
        "education_linked": education,
        "social_care_linked": social,
        "linkage_table": linkage,
        "linkage_summary": basic_linkage,
        "metadata_catalogue": catalogue,
        "variable_quality_metrics": metrics,
        "quality_issues": issues,
        "quality_rule_summary": rule_summary,
        "phenotype_flags": phenotype_flags,
        "phenotype_prevalence": phenotype_prevalence,
        "data_refresh_log": refresh_log,
        "release_diff": release_diff,
        "data_source_trends": source_trends,
        "education_missingness_by_year": education_missingness,
        "social_missingness_by_region": social_missingness,
        **linkage_outputs,
    }
    for name, frame in tables.items():
        _write(frame, processed / f"{name}.csv")

    _write_sqlite(
        processed,
        {
            "children": children,
            "health_episodes": health,
            "education_records": education,
            "social_care_events": social,
            "linkage_summary": basic_linkage,
            "metadata_catalogue": catalogue,
            "variable_quality_metrics": metrics,
            "quality_rule_summary": rule_summary,
            "phenotype_prevalence": phenotype_prevalence,
            "release_diff": release_diff,
            "linkage_evaluation_summary": linkage_outputs["linkage_evaluation_summary"],
        },
    )


if __name__ == "__main__":
    build_processed(Path(__file__).resolve().parents[1])
