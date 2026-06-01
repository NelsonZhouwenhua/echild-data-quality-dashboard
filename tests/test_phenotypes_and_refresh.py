from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def test_executable_phenotype_outputs_exist():
    phenotype = pd.read_csv(P / "phenotype_prevalence.csv")
    assert set(phenotype["phenotype"]) == {
        "persistent_school_absence",
        "recurrent_hospital_admission",
        "chronic_condition_group",
    }
    assert phenotype["eligible_children"].gt(0).all()
    assert phenotype["prevalence_among_eligible"].between(0, 1).all()


def test_release_comparison_adds_2025_coverage():
    releases = pd.read_csv(P / "release_diff.csv")
    assert set(releases["source"]) == {"health", "education", "social_care"}
    assert releases["current_coverage"].str.endswith("2025").all()
