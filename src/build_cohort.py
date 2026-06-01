"""Cohort-feasibility logic for the interactive public portfolio dashboard."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class CohortFilters:
    """User-selectable cohort design fields."""

    cohort_design: str = "Index hospital-admission cohort"
    birth_year_min: int = 2010
    birth_year_max: int = 2015
    regions: tuple[str, ...] = ()
    deprivation_quintiles: tuple[int, ...] = ()
    min_follow_up_years: int = 2
    index_year_min: int = 2018
    index_year_max: int = 2022
    school_inception_year: int = 2020
    diagnosis_group: str | None = "Respiratory"
    require_health: bool = True
    require_education: bool = True
    require_social_care: bool = False
    outcome_phenotype: str = "persistent_school_absence"


def _linked_ids(frame: pd.DataFrame) -> set[str]:
    return set(frame["linked_child_id"].dropna().astype(str).unique())


def _append_attrition(rows: list[dict[str, Any]], step: str, description: str, before: int, after: int) -> None:
    rows.append(
        {
            "step": step,
            "description": description,
            "input_children": int(before),
            "retained_children": int(after),
            "removed_children": int(before - after),
        }
    )


def _filter_ids(cohort: pd.DataFrame, child_ids: set[str], rows: list[dict[str, Any]], step: str, description: str) -> pd.DataFrame:
    before = len(cohort)
    cohort = cohort[cohort["child_id"].isin(child_ids)].copy()
    _append_attrition(rows, step, description, before, len(cohort))
    return cohort


def _outcome_eligible_ids(education: pd.DataFrame, outcome_phenotype: str) -> set[str]:
    if outcome_phenotype == "persistent_school_absence":
        valid = education[
            education["linked_child_id"].notna()
            & education["attendance_rate"].notna()
            & education["attendance_rate"].between(0, 1)
        ]
        return _linked_ids(valid)
    return _linked_ids(education)


def build_cohort(
    children: pd.DataFrame,
    health: pd.DataFrame,
    education: pd.DataFrame,
    social: pd.DataFrame,
    filters: CohortFilters,
    as_of_year: int = 2025,
    linkage_by_deprivation: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Create a cohort-spine feasibility summary.

    The returned `cohort` object supports internal calculations but should not
    be rendered by the public dashboard. Only aggregate outputs are shown.
    """

    cohort = children.copy()
    cohort["birth_year"] = cohort["birth_date"].dt.year
    cohort["follow_up_years"] = as_of_year - cohort["birth_year"]
    attrition: list[dict[str, Any]] = []
    _append_attrition(attrition, "Population spine", "All synthetic children", len(cohort), len(cohort))

    before = len(cohort)
    cohort = cohort[cohort["birth_year"].between(filters.birth_year_min, filters.birth_year_max)].copy()
    _append_attrition(attrition, "Birth-year eligibility", f"Born between {filters.birth_year_min} and {filters.birth_year_max}", before, len(cohort))

    before = len(cohort)
    cohort = cohort[cohort["follow_up_years"] >= filters.min_follow_up_years].copy()
    _append_attrition(attrition, "Follow-up eligibility", f"At least {filters.min_follow_up_years} years of potential follow-up", before, len(cohort))

    if filters.regions:
        before = len(cohort)
        cohort = cohort[cohort["region"].isin(filters.regions)].copy()
        _append_attrition(attrition, "Region filter", ", ".join(filters.regions), before, len(cohort))

    if filters.deprivation_quintiles:
        before = len(cohort)
        cohort = cohort[cohort["deprivation_quintile"].isin(filters.deprivation_quintiles)].copy()
        selected = ", ".join(str(value) for value in filters.deprivation_quintiles)
        _append_attrition(attrition, "Deprivation filter", f"Selected quintiles: {selected}", before, len(cohort))

    index_events = pd.DataFrame(columns=["linked_child_id", "index_date"])
    if filters.cohort_design == "Index hospital-admission cohort":
        qualifying = health[
            health["linked_child_id"].notna()
            & health["admission_date"].dt.year.between(filters.index_year_min, filters.index_year_max)
        ].copy()
        if filters.diagnosis_group:
            qualifying = qualifying[qualifying["diagnosis_group"].eq(filters.diagnosis_group)].copy()
        index_events = (
            qualifying.groupby("linked_child_id", as_index=False)["admission_date"]
            .min()
            .rename(columns={"admission_date": "index_date"})
        )
        description = f"First {filters.diagnosis_group or 'qualifying'} admission during {filters.index_year_min}-{filters.index_year_max}"
        cohort = _filter_ids(cohort, set(index_events["linked_child_id"].astype(str)), attrition, "Index admission", description)
    elif filters.cohort_design == "School inception cohort":
        qualifying = education[
            education["linked_child_id"].notna()
            & education["academic_year"].eq(filters.school_inception_year)
        ].copy()
        cohort = _filter_ids(
            cohort,
            _linked_ids(qualifying),
            attrition,
            "School inception",
            f"Linked education record in academic year {filters.school_inception_year}",
        )
    elif filters.cohort_design == "Birth cohort":
        before = len(cohort)
        _append_attrition(attrition, "Birth cohort spine", "No additional index-event restriction", before, len(cohort))
    else:
        raise ValueError(f"Unsupported cohort design: {filters.cohort_design}")

    if filters.require_health and filters.cohort_design != "Index hospital-admission cohort":
        cohort = _filter_ids(cohort, _linked_ids(health), attrition, "Linked health module", "At least one matched health record")
    if filters.require_education:
        cohort = _filter_ids(cohort, _linked_ids(education), attrition, "Linked education module", "At least one matched education record")
    if filters.require_social_care:
        cohort = _filter_ids(cohort, _linked_ids(social), attrition, "Linked social-care module", "At least one matched social-care record")

    if filters.outcome_phenotype:
        cohort = _filter_ids(
            cohort,
            _outcome_eligible_ids(education, filters.outcome_phenotype),
            attrition,
            "Valid outcome availability",
            f"Sufficient valid records to derive {filters.outcome_phenotype}",
        )

    if not index_events.empty:
        cohort = cohort.merge(index_events, left_on="child_id", right_on="linked_child_id", how="left").drop(columns=["linked_child_id"])

    child_ids = set(cohort["child_id"].astype(str))
    health_subset = health[health["linked_child_id"].astype("string").isin(child_ids)].copy()
    education_subset = education[education["linked_child_id"].astype("string").isin(child_ids)].copy()
    social_subset = social[social["linked_child_id"].astype("string").isin(child_ids)].copy()

    warnings: list[str] = []
    attendance_2020 = education_subset.loc[education_subset["academic_year"].eq(2020), "attendance_rate"]
    if len(attendance_2020) and float(attendance_2020.isna().mean()) > 0.15:
        warnings.append("Attendance completeness is lower during academic year 2020. Consider a sensitivity analysis excluding 2020.")
    if linkage_by_deprivation is not None and not linkage_by_deprivation.empty:
        edu = linkage_by_deprivation[linkage_by_deprivation["source"].eq("education")]
        if not edu.empty and float(edu["linkage_rate"].max() - edu["linkage_rate"].min()) > 0.02:
            warnings.append("Education linkage rates differ across deprivation quintiles. Compare linked and unlinked groups before interpreting subgroup results.")
    if len(cohort) < 200:
        warnings.append("The selected cohort is small. Some subgroup outputs may be suppressed or unstable.")
    if filters.require_social_care and social_subset.empty:
        warnings.append("No linked social-care records are available for this selection.")
    warnings.append("This is a descriptive feasibility assessment using synthetic data. It is not a causal-effect estimate.")

    summary = {
        "initial_population_spine": int(len(children)),
        "final_analytical_cohort": int(len(cohort)),
        "health_records": int(len(health_subset)),
        "education_records": int(len(education_subset)),
        "social_care_records": int(len(social_subset)),
        "children_with_health": int(health_subset["linked_child_id"].nunique()),
        "children_with_education": int(education_subset["linked_child_id"].nunique()),
        "children_with_social_care": int(social_subset["linked_child_id"].nunique()),
        "median_follow_up_years": float(cohort["follow_up_years"].median()) if len(cohort) else 0.0,
        "education_attendance_missing_rate": float(education_subset["attendance_rate"].isna().mean()) if len(education_subset) else 0.0,
    }
    manifest = {
        "research_question": "Persistent school absence after hospital admission",
        "cohort_design": filters.cohort_design,
        "filters": asdict(filters),
        "required_sources": [
            source
            for source, required in {
                "health_admissions": filters.require_health or filters.cohort_design == "Index hospital-admission cohort",
                "education_attendance": filters.require_education or bool(filters.outcome_phenotype),
                "social_care_events": filters.require_social_care,
            }.items()
            if required
        ],
        "required_variables": [
            "linked_child_id",
            "birth_year",
            "deprivation_quintile",
            "region",
            "admission_date",
            "diagnosis_group",
            "academic_year",
            "term",
            "attendance_rate",
        ],
        "aggregate_summary": summary,
        "known_limitations": warnings,
        "public_output_note": "Aggregate-only synthetic portfolio output. Row-level extracts are not exposed.",
    }
    return {
        "summary": summary,
        "warnings": warnings,
        "attrition": pd.DataFrame(attrition),
        "manifest": manifest,
        "cohort": cohort,
        "health_subset": health_subset,
        "education_subset": education_subset,
        "social_subset": social_subset,
    }


def render_feasibility_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    warnings = "\n".join(f"- {warning}" for warning in result["warnings"])
    attrition = result["attrition"].to_markdown(index=False)
    return f"""# Synthetic linked child-data feasibility report

> Synthetic demonstration only. No restricted administrative records are used.

## Aggregate cohort summary

- Initial population spine: {summary['initial_population_spine']:,}
- Final analytical cohort: {summary['final_analytical_cohort']:,}
- Health records in scope: {summary['health_records']:,}
- Education records in scope: {summary['education_records']:,}
- Social-care records in scope: {summary['social_care_records']:,}
- Median potential follow-up: {summary['median_follow_up_years']:.1f} years

## Cohort attrition

{attrition}

## Feasibility warnings

{warnings}

## Governance note

This public portfolio report contains aggregate synthetic outputs only. A row-level extract would remain inside an approved trusted research environment.
"""


def render_manifest_yaml(result: dict[str, Any]) -> str:
    return yaml.safe_dump(result["manifest"], sort_keys=False, allow_unicode=True)
