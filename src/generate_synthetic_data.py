"""Generate a fully synthetic linked child administrative-data resource.

The generated records are invented for a public portfolio demonstration. They
are not copied from ECHILD, Hospital Episode Statistics (HES), the National
Pupil Database (NPD), or children's social-care records. Deliberate quality
issues are added so that audit and feasibility workflows have useful cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SyntheticConfig:
    """Configuration for the synthetic data generator."""

    n_children: int = 5_000
    seed: int = 20260601
    start_year: int = 2016
    end_year: int = 2025


REGIONS = [
    "London",
    "North East",
    "North West",
    "Yorkshire and The Humber",
    "East Midlands",
    "West Midlands",
    "South East",
    "South West",
]
SEXES = ["Female", "Male"]
ETHNICITY_GROUPS = ["Asian", "Black", "Mixed", "Other", "White", "Not recorded"]
DIAGNOSES = ["Respiratory", "Injury", "Infection", "Mental health", "Neurology", "Other"]
ADMISSION_TYPES = ["Emergency", "Elective", "Day case"]
SOCIAL_EVENT_TYPES = ["Referral", "Assessment", "Child in need plan", "Review"]
SOCIAL_REASONS = ["Family support", "Safeguarding", "Disability support", "Housing", "Other"]
ASSESSMENT_OUTCOMES = ["No further action", "Support offered", "Plan opened", "Referred onward"]
TERMS = ["Autumn", "Spring", "Summer"]


def _random_dates(rng: np.random.Generator, start: str, end: str, n: int) -> pd.Series:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    days = int((end_ts - start_ts).days)
    offsets = rng.integers(0, days + 1, size=n)
    return pd.Series(pd.to_datetime(start_ts + pd.to_timedelta(offsets, unit="D")))


def _school_stage(age: pd.Series) -> pd.Series:
    conditions = [age < 5, age.between(5, 10), age.between(11, 15), age >= 16]
    values = ["Pre-school", "Primary", "Secondary", "Post-16"]
    return pd.Series(np.select(conditions, values, default="Unknown"), index=age.index)


def _append_duplicates(
    df: pd.DataFrame,
    truth: pd.DataFrame,
    rng: np.random.Generator,
    frac: float,
    row_prefix: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Append rows with new row IDs but repeated source record IDs."""

    n_dup = max(1, int(len(df) * frac))
    duplicate_idx = rng.choice(df.index, size=n_dup, replace=False)
    duplicates = df.loc[duplicate_idx].copy()
    duplicate_truth = truth.loc[duplicate_idx].copy()
    new_rows = [f"{row_prefix}D{i:08d}" for i in range(1, n_dup + 1)]
    duplicates["source_row_id"] = new_rows
    duplicate_truth["source_row_id"] = new_rows
    return pd.concat([df, duplicates], ignore_index=True), pd.concat([truth, duplicate_truth], ignore_index=True)


def generate_children(cfg: SyntheticConfig, rng: np.random.Generator) -> pd.DataFrame:
    children = pd.DataFrame(
        {
            "child_id": [f"C{i:07d}" for i in range(1, cfg.n_children + 1)],
            "birth_date": _random_dates(rng, "2008-01-01", "2018-12-31", cfg.n_children),
            "sex": rng.choice(SEXES, size=cfg.n_children, p=[0.49, 0.51]),
            "region": rng.choice(REGIONS, size=cfg.n_children),
            "deprivation_quintile": rng.integers(1, 6, size=cfg.n_children),
            "ethnicity_group": rng.choice(
                ETHNICITY_GROUPS,
                size=cfg.n_children,
                p=[0.12, 0.07, 0.05, 0.04, 0.68, 0.04],
            ),
        }
    )
    la_suffix = pd.Series(rng.integers(1, 31, size=cfg.n_children)).astype(str).str.zfill(2)
    children["local_authority_code"] = (
        children["region"].str.replace(" ", "", regex=False).str[:3].str.upper() + la_suffix
    )
    return children


def generate_health(
    children: pd.DataFrame, cfg: SyntheticConfig, rng: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = int(cfg.n_children * 2.45)
    truth_ids = rng.choice(children["child_id"], size=n, replace=True)
    births = children.set_index("child_id").loc[truth_ids, "birth_date"].reset_index(drop=True)
    admission_dates = _random_dates(rng, f"{cfg.start_year}-01-01", f"{cfg.end_year}-12-31", n)
    admission_dates = pd.Series(
        np.maximum(admission_dates.values.astype("datetime64[ns]"), births.values.astype("datetime64[ns]"))
    )
    lengths = rng.integers(0, 15, size=n)
    discharge_dates = admission_dates + pd.to_timedelta(lengths, unit="D")
    row_ids = [f"HR{i:09d}" for i in range(1, n + 1)]
    record_ids = [f"H{i:08d}" for i in range(1, n + 1)]
    health = pd.DataFrame(
        {
            "source_row_id": row_ids,
            "source_record_id": record_ids,
            "source_person_id": [f"HP{value[1:]}" for value in truth_ids],
            "admission_date": admission_dates,
            "discharge_date": discharge_dates,
            "diagnosis_group": rng.choice(DIAGNOSES, size=n, p=[0.22, 0.20, 0.22, 0.12, 0.08, 0.16]),
            "admission_type": rng.choice(ADMISSION_TYPES, size=n, p=[0.55, 0.28, 0.17]),
            "provider_code": [f"TRUST{value:03d}" for value in rng.integers(1, 90, size=n)],
        }
    )
    truth = pd.DataFrame(
        {
            "source": "health",
            "source_row_id": row_ids,
            "source_record_id": record_ids,
            "true_child_id": truth_ids,
        }
    )

    bad_prebirth = rng.choice(health.index, size=max(1, int(n * 0.004)), replace=False)
    health.loc[bad_prebirth, "admission_date"] = births.iloc[bad_prebirth].values - pd.to_timedelta(
        rng.integers(1, 180, size=len(bad_prebirth)), unit="D"
    )
    health.loc[bad_prebirth, "discharge_date"] = health.loc[bad_prebirth, "admission_date"] + pd.to_timedelta(
        1, unit="D"
    )
    bad_discharge = rng.choice(
        health.index.difference(bad_prebirth), size=max(1, int(n * 0.003)), replace=False
    )
    health.loc[bad_discharge, "discharge_date"] = health.loc[bad_discharge, "admission_date"] - pd.to_timedelta(
        rng.integers(1, 7, size=len(bad_discharge)), unit="D"
    )
    missing_diag = rng.choice(health.index, size=max(1, int(n * 0.02)), replace=False)
    health.loc[missing_diag, "diagnosis_group"] = pd.NA
    return _append_duplicates(health, truth, rng, 0.012, "HR")


def generate_education(
    children: pd.DataFrame, cfg: SyntheticConfig, rng: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    truth_frames: list[pd.DataFrame] = []
    record_number = 1
    # Stable child-level absence risk makes the executable phenotype example
    # more realistic than independent term-level draws. Risk is still fully
    # synthetic and slightly higher in more deprived quintiles.
    absence_probability = 0.055 + 0.018 * (children["deprivation_quintile"] - 1)
    high_absence = rng.random(len(children)) < absence_probability.to_numpy()
    high_absence_ids = set(children.loc[high_absence, "child_id"].astype(str))
    for year in range(2017, cfg.end_year + 1):
        age = year - children["birth_date"].dt.year
        eligible = children.loc[age.between(5, 17)].copy()
        if eligible.empty:
            continue
        for term in TERMS:
            selected = eligible.sample(frac=0.88, random_state=int(rng.integers(1, 1_000_000)))
            n = len(selected)
            selected_age = year - selected["birth_date"].dt.year
            row_ids = [f"ER{i:010d}" for i in range(record_number, record_number + n)]
            record_ids = [f"E{i:09d}" for i in range(record_number, record_number + n)]
            child_ids = selected["child_id"].to_numpy()
            is_high_absence = np.array([str(value) in high_absence_ids for value in child_ids])
            attendance = np.empty(n, dtype=float)
            attendance[~is_high_absence] = rng.beta(58, 2.2, size=int((~is_high_absence).sum()))
            attendance[is_high_absence] = rng.beta(16, 4.6, size=int(is_high_absence.sum()))
            frame = pd.DataFrame(
                {
                    "source_row_id": row_ids,
                    "source_record_id": record_ids,
                    "source_person_id": [f"EP{value[1:]}" for value in child_ids],
                    "academic_year": year,
                    "term": term,
                    "school_stage": _school_stage(selected_age).to_numpy(),
                    "attendance_rate": np.round(np.clip(attendance, 0, 1), 4),
                    "sen_support": rng.choice(["No", "Yes", "Not recorded"], size=n, p=[0.78, 0.18, 0.04]),
                    "school_code": [f"SCH{value:04d}" for value in rng.integers(1, 800, size=n)],
                }
            )
            truth = pd.DataFrame(
                {
                    "source": "education",
                    "source_row_id": row_ids,
                    "source_record_id": record_ids,
                    "true_child_id": child_ids,
                }
            )
            frames.append(frame)
            truth_frames.append(truth)
            record_number += n
    education = pd.concat(frames, ignore_index=True)
    truth = pd.concat(truth_frames, ignore_index=True)

    mask_2020 = education["academic_year"].eq(2020)
    missing_2020 = education.loc[mask_2020].sample(frac=0.22, random_state=cfg.seed).index
    missing_other = education.loc[~mask_2020].sample(frac=0.035, random_state=cfg.seed + 1).index
    education.loc[missing_2020.union(missing_other), "attendance_rate"] = np.nan
    invalid = education.sample(frac=0.004, random_state=cfg.seed + 2).index
    education.loc[invalid, "attendance_rate"] = 1.15
    mismatched = education.sample(frac=0.006, random_state=cfg.seed + 3).index
    education.loc[mismatched, "school_stage"] = "Post-16"
    return _append_duplicates(education, truth, rng, 0.006, "ER")


def generate_social_care(
    children: pd.DataFrame, cfg: SyntheticConfig, rng: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = children.sample(frac=0.26, random_state=cfg.seed + 5).reset_index(drop=True)
    counts = rng.integers(1, 5, size=len(selected))
    expanded = selected.loc[selected.index.repeat(counts)].reset_index(drop=True)
    n = len(expanded)
    row_ids = [f"SR{i:09d}" for i in range(1, n + 1)]
    record_ids = [f"S{i:08d}" for i in range(1, n + 1)]
    referral = _random_dates(rng, f"{cfg.start_year}-01-01", f"{cfg.end_year}-12-31", n)
    referral = pd.Series(
        np.maximum(referral.values.astype("datetime64[ns]"), expanded["birth_date"].values.astype("datetime64[ns]"))
    )
    social = pd.DataFrame(
        {
            "source_row_id": row_ids,
            "source_record_id": record_ids,
            "source_person_id": [f"SP{value[1:]}" for value in expanded["child_id"]],
            "referral_date": referral,
            "event_type": rng.choice(SOCIAL_EVENT_TYPES, size=n),
            "reason_group": rng.choice(SOCIAL_REASONS, size=n),
            "assessment_outcome": rng.choice(ASSESSMENT_OUTCOMES, size=n),
            "local_authority_region": expanded["region"].to_numpy(),
        }
    )
    truth = pd.DataFrame(
        {
            "source": "social_care",
            "source_row_id": row_ids,
            "source_record_id": record_ids,
            "true_child_id": expanded["child_id"].to_numpy(),
        }
    )

    high_missing = social["local_authority_region"].isin(["North East", "West Midlands"])
    sample_hi = social.loc[high_missing].sample(frac=0.24, random_state=cfg.seed + 6).index
    sample_lo = social.loc[~high_missing].sample(frac=0.08, random_state=cfg.seed + 7).index
    social.loc[sample_hi.union(sample_lo), "assessment_outcome"] = pd.NA
    prebirth = social.sample(frac=0.003, random_state=cfg.seed + 8).index
    social.loc[prebirth, "referral_date"] = expanded.loc[prebirth, "birth_date"].values - pd.to_timedelta(
        rng.integers(1, 90, size=len(prebirth)), unit="D"
    )
    return _append_duplicates(social, truth, rng, 0.01, "SR")


def _random_incorrect_ids(
    true_ids: pd.Series, all_child_ids: np.ndarray, rng: np.random.Generator
) -> pd.Series:
    """Generate linked IDs that differ from the true child IDs."""

    selected = rng.choice(all_child_ids, size=len(true_ids), replace=True)
    same = selected == true_ids.to_numpy()
    while same.any():
        selected[same] = rng.choice(all_child_ids, size=int(same.sum()), replace=True)
        same = selected == true_ids.to_numpy()
    return pd.Series(selected, index=true_ids.index)


def generate_linkage(
    truth: pd.DataFrame, children: pd.DataFrame, cfg: SyntheticConfig, rng: np.random.Generator
) -> pd.DataFrame:
    """Create synthetic linkage outcomes, including a small false-link rate.

    `match_status` is the operational status available to an analyst. The
    internal truth file permits aggregate linkage evaluation for this public
    demonstration. It is never presented as a real-world ground truth model.
    """

    merged = truth.merge(
        children[["child_id", "deprivation_quintile", "region"]],
        left_on="true_child_id",
        right_on="child_id",
        how="left",
    )
    base_match = merged["source"].map({"health": 0.972, "education": 0.955, "social_care": 0.900}).astype(float)
    ambiguous_prob = merged["source"].map({"health": 0.010, "education": 0.012, "social_care": 0.030}).astype(float)
    false_link_prob = merged["source"].map({"health": 0.006, "education": 0.010, "social_care": 0.020}).astype(float)
    deprivation_penalty = -0.005 * (merged["deprivation_quintile"] - 1)
    social_region_penalty = (
        (merged["source"] == "social_care")
        & merged["region"].isin(["North East", "West Midlands"])
    ).astype(float) * -0.020
    match_prob = np.clip(base_match + deprivation_penalty + social_region_penalty, 0.70, 0.995)

    u = rng.random(len(merged))
    matched = u < match_prob
    ambiguous = (~matched) & (u < match_prob + ambiguous_prob)
    unmatched = ~(matched | ambiguous)
    status = np.where(matched, "matched", np.where(ambiguous, "ambiguous", "unmatched"))

    false_link = matched & (rng.random(len(merged)) < false_link_prob)
    linked_id = merged["true_child_id"].astype("string").copy()
    if false_link.any():
        linked_id.loc[false_link] = _random_incorrect_ids(
            merged.loc[false_link, "true_child_id"], children["child_id"].to_numpy(), rng
        )
    linked_id.loc[~matched] = pd.NA

    confidence = np.empty(len(merged), dtype=float)
    correct = matched & ~false_link
    confidence[correct] = np.clip(rng.normal(0.970, 0.020, int(correct.sum())), 0.82, 1.00)
    confidence[false_link] = np.clip(rng.normal(0.850, 0.060, int(false_link.sum())), 0.62, 0.97)
    confidence[ambiguous] = np.clip(rng.normal(0.620, 0.080, int(ambiguous.sum())), 0.35, 0.82)
    confidence[unmatched] = np.clip(rng.normal(0.220, 0.100, int(unmatched.sum())), 0.00, 0.50)
    candidate_count = np.where(matched, 1, np.where(ambiguous, rng.integers(2, 5, size=len(merged)), 0))

    return pd.DataFrame(
        {
            "source": merged["source"],
            "source_row_id": merged["source_row_id"],
            "source_record_id": merged["source_record_id"],
            "linked_child_id": linked_id,
            "match_status": status,
            "linkage_confidence": np.round(confidence, 4),
            "candidate_count": candidate_count,
        }
    )


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def generate_all(output_dir: Path, config: SyntheticConfig | None = None) -> None:
    cfg = config or SyntheticConfig()
    rng = np.random.default_rng(cfg.seed)
    raw_dir = output_dir / "data" / "raw"
    internal_dir = output_dir / "data" / "internal"
    raw_dir.mkdir(parents=True, exist_ok=True)
    internal_dir.mkdir(parents=True, exist_ok=True)

    children = generate_children(cfg, rng)
    health, health_truth = generate_health(children, cfg, rng)
    education, education_truth = generate_education(children, cfg, rng)
    social, social_truth = generate_social_care(children, cfg, rng)
    truth = pd.concat([health_truth, education_truth, social_truth], ignore_index=True)
    linkage = generate_linkage(truth, children, cfg, rng)

    _write(children, raw_dir / "children.csv")
    _write(health, raw_dir / "health_episodes.csv")
    _write(education, raw_dir / "education_records.csv")
    _write(social, raw_dir / "social_care_events.csv")
    _write(linkage, raw_dir / "linkage_table.csv")
    _write(truth, internal_dir / "linkage_truth.csv")


if __name__ == "__main__":
    generate_all(Path(__file__).resolve().parents[1])
