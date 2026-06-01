from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"


def test_linkage_order_is_plausible():
    summary = pd.read_csv(P / "linkage_evaluation_summary.csv").set_index("source")
    assert summary.loc["health", "linkage_rate"] > summary.loc["education", "linkage_rate"] > summary.loc["social_care", "linkage_rate"]


def test_linkage_evaluation_contains_false_links():
    summary = pd.read_csv(P / "linkage_evaluation_summary.csv")
    assert summary["false_links"].sum() > 0
    assert summary["precision"].between(0.9, 1.0).all()


def test_education_linkage_rate_varies_by_deprivation():
    subgroup = pd.read_csv(P / "linkage_by_deprivation.csv")
    education = subgroup[subgroup["source"] == "education"]
    assert education["linkage_rate"].max() - education["linkage_rate"].min() > 0.01
