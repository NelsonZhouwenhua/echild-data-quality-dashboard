from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def test_expected_quality_issues_are_detected():
    issues = pd.read_csv(P / "quality_issues.csv")
    checks = set(issues["check_name"])
    assert "duplicate_source_record_id" in checks
    assert "admission_before_birth" in checks
    assert "discharge_before_admission" in checks
    assert "attendance_out_of_range" in checks
    assert "school_stage_age_inconsistency" in checks
    assert "referral_before_birth" in checks


def test_education_2020_missingness_is_higher():
    education = pd.read_csv(P / "education_linked.csv")
    rates = education.groupby("academic_year")["attendance_rate"].apply(lambda series: series.isna().mean())
    assert rates.loc[2020] > rates.drop(index=2020).mean() + 0.10


def test_rule_registry_has_recommended_actions():
    rules = pd.read_csv(P / "quality_rule_summary.csv")
    assert len(rules) >= 8
    assert rules["recommended_action"].notna().all()
    assert set(rules["category"]) >= {"completeness", "validity", "consistency", "duplication"}
