from pathlib import Path

import pandas as pd

from src.build_cohort import CohortFilters, build_cohort, render_feasibility_report, render_manifest_yaml

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def load():
    children = pd.read_csv(P / "children.csv", parse_dates=["birth_date"])
    health = pd.read_csv(P / "health_linked.csv", parse_dates=["admission_date", "discharge_date"])
    education = pd.read_csv(P / "education_linked.csv")
    social = pd.read_csv(P / "social_care_linked.csv", parse_dates=["referral_date"])
    linkage_by_deprivation = pd.read_csv(P / "linkage_by_deprivation.csv")
    return children, health, education, social, linkage_by_deprivation


def test_index_admission_cohort_returns_attrition_and_summary():
    children, health, education, social, linkage = load()
    result = build_cohort(
        children,
        health,
        education,
        social,
        CohortFilters(
            cohort_design="Index hospital-admission cohort",
            birth_year_min=2010,
            birth_year_max=2015,
            diagnosis_group="Respiratory",
            index_year_min=2018,
            index_year_max=2022,
            require_education=True,
        ),
        linkage_by_deprivation=linkage,
    )
    assert result["summary"]["final_analytical_cohort"] > 0
    assert "Index admission" in set(result["attrition"]["step"])
    assert "Valid outcome availability" in set(result["attrition"]["step"])
    assert any("descriptive feasibility" in warning for warning in result["warnings"])


def test_public_report_has_no_child_identifiers():
    children, health, education, social, linkage = load()
    result = build_cohort(children, health, education, social, CohortFilters(), linkage_by_deprivation=linkage)
    report = render_feasibility_report(result)
    manifest = render_manifest_yaml(result)
    assert "C000" not in report
    assert "C000" not in manifest
    assert "Row-level" in report or "row-level" in report
