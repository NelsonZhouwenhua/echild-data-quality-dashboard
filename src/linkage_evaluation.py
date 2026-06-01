"""Aggregate linkage evaluation for the fully synthetic resource."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _decorate_linkage(linkage: pd.DataFrame, truth: pd.DataFrame, children: pd.DataFrame) -> pd.DataFrame:
    merged = linkage.merge(
        truth[["source", "source_row_id", "true_child_id"]],
        on=["source", "source_row_id"],
        how="left",
        validate="one_to_one",
    )
    merged = merged.merge(
        children[["child_id", "region", "deprivation_quintile"]],
        left_on="true_child_id",
        right_on="child_id",
        how="left",
        validate="many_to_one",
    )
    merged["is_matched"] = merged["match_status"].eq("matched")
    merged["is_ambiguous"] = merged["match_status"].eq("ambiguous")
    merged["is_unmatched"] = merged["match_status"].eq("unmatched")
    merged["is_correct_link"] = merged["is_matched"] & merged["linked_child_id"].eq(merged["true_child_id"])
    merged["is_false_link"] = merged["is_matched"] & ~merged["linked_child_id"].eq(merged["true_child_id"])
    merged["is_missed_link"] = ~merged["is_matched"]
    return merged


def _summarise(grouped: pd.core.groupby.generic.DataFrameGroupBy) -> pd.DataFrame:
    summary = grouped.agg(
        records=("source_row_id", "size"),
        matched=("is_matched", "sum"),
        correct_links=("is_correct_link", "sum"),
        false_links=("is_false_link", "sum"),
        missed_links=("is_missed_link", "sum"),
        ambiguous=("is_ambiguous", "sum"),
        unmatched=("is_unmatched", "sum"),
        mean_confidence=("linkage_confidence", "mean"),
    ).reset_index()
    summary["linkage_rate"] = np.where(summary["records"] > 0, summary["matched"] / summary["records"], 0.0)
    summary["precision"] = np.where(summary["matched"] > 0, summary["correct_links"] / summary["matched"], 0.0)
    summary["recall"] = np.where(
        (summary["correct_links"] + summary["missed_links"]) > 0,
        summary["correct_links"] / (summary["correct_links"] + summary["missed_links"]),
        0.0,
    )
    summary["false_link_rate"] = np.where(summary["records"] > 0, summary["false_links"] / summary["records"], 0.0)
    return summary


def evaluate_linkage(
    linkage: pd.DataFrame,
    truth: pd.DataFrame,
    children: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Produce source and subgroup linkage summaries from synthetic truth."""

    decorated = _decorate_linkage(linkage, truth, children)
    source_summary = _summarise(decorated.groupby(["source"], dropna=False))
    by_deprivation = _summarise(decorated.groupby(["source", "deprivation_quintile"], dropna=False))
    by_region = _summarise(decorated.groupby(["source", "region"], dropna=False))

    bins = [0.0, 0.5, 0.7, 0.85, 0.95, 1.0001]
    labels = ["0.00-0.49", "0.50-0.69", "0.70-0.84", "0.85-0.94", "0.95-1.00"]
    decorated["confidence_band"] = pd.cut(
        decorated["linkage_confidence"], bins=bins, labels=labels, right=False, include_lowest=True
    )
    by_confidence = _summarise(decorated.groupby(["source", "confidence_band"], observed=False, dropna=False))
    return {
        "linkage_evaluation_summary": source_summary,
        "linkage_by_deprivation": by_deprivation,
        "linkage_by_region": by_region,
        "linkage_by_confidence": by_confidence,
    }
