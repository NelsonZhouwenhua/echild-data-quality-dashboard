"""Generate reviewer-facing aggregate reports and a static dashboard preview."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.build_cohort import CohortFilters, build_cohort, render_feasibility_report, render_manifest_yaml
from src.disclosure_control import suppress_small_counts


def _read(path: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(path, **kwargs)


def _pct(value: float) -> str:
    return f"{100 * float(value):.1f}%"


def _table(frame: pd.DataFrame) -> str:
    return frame.to_html(index=False, border=0, classes="data-table", escape=True)


def _write_markdown_reports(root: Path, data: dict[str, pd.DataFrame], feasibility: dict) -> None:
    docs = root / "docs"
    outputs = root / "outputs"
    docs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    linkage = data["linkage_eval"].copy()
    for column in ["linkage_rate", "precision", "recall", "false_link_rate"]:
        linkage[column] = linkage[column].map(_pct)
    quality = data["rule_summary"].copy()
    quality = quality.sort_values(["status", "severity", "flagged_records"], ascending=[False, True, False])
    phenotype = data["phenotype_prevalence"].copy()
    phenotype["prevalence_among_eligible"] = phenotype["prevalence_among_eligible"].map(_pct)
    phenotype["coverage_of_spine"] = phenotype["coverage_of_spine"].map(_pct)

    linkage_report = f"""# Synthetic linkage-quality report

> Synthetic demonstration only. This report does not use ECHILD, HES, NPD or children's social-care records.

## Source-level linkage evaluation

{linkage.to_markdown(index=False)}

## Linkage-rate variation by deprivation quintile

{data['linkage_by_deprivation'].to_markdown(index=False)}

## Interpretation note

The internal synthetic truth file is used only to test the portfolio workflow. Real administrative-data linkage evaluation requires project-specific methods, approved access arrangements and careful reporting of possible linkage bias.
"""
    (docs / "linkage_quality_report.md").write_text(linkage_report, encoding="utf-8")

    quality_report = f"""# Synthetic data-quality audit report

> Synthetic demonstration only. The rules are illustrative and should be adapted to the approved data environment and research question.

## Quality-rule registry summary

{quality.to_markdown(index=False)}

## Attendance missingness by academic year

{data['education_missingness'].to_markdown(index=False)}

## Social-care assessment-outcome missingness by region

{data['social_missingness'].to_markdown(index=False)}
"""
    (docs / "data_quality_report.md").write_text(quality_report, encoding="utf-8")

    phenotype_report = f"""# Executable synthetic phenotype examples

> These examples use simplified synthetic variables. They are not clinical code lists.

{phenotype.to_markdown(index=False)}
"""
    (docs / "phenotype_report.md").write_text(phenotype_report, encoding="utf-8")

    refresh_report = f"""# Synthetic data-refresh comparison

> Synthetic demonstration only.

{data['release_diff'].to_markdown(index=False)}

## Review note

A refresh workflow should confirm that expected modules, variables and years are present before a new release is used for research extracts.
"""
    (docs / "data_refresh_report.md").write_text(refresh_report, encoding="utf-8")

    (outputs / "feasibility_report.md").write_text(render_feasibility_report(feasibility), encoding="utf-8")
    feasibility["attrition"].to_csv(outputs / "cohort_attrition.csv", index=False)
    (outputs / "extract_manifest.yml").write_text(render_manifest_yaml(feasibility), encoding="utf-8")
    data["linkage_eval"].to_csv(outputs / "linkage_evaluation_summary.csv", index=False)
    data["rule_summary"].to_csv(outputs / "quality_rule_summary.csv", index=False)
    data["release_diff"].to_csv(outputs / "release_diff.csv", index=False)
    data["phenotype_prevalence"].to_csv(outputs / "phenotype_prevalence.csv", index=False)


def _preview_html(root: Path, data: dict[str, pd.DataFrame], feasibility: dict) -> None:
    outputs = root / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    children = data["children"]
    health = data["health"]
    education = data["education"]
    social = data["social"]
    issues = data["issues"]

    linkage = data["linkage_eval"].copy()
    for column in ["linkage_rate", "precision", "recall", "false_link_rate"]:
        linkage[column] = linkage[column].map(_pct)
    linkage = linkage[["source", "records", "matched", "correct_links", "false_links", "ambiguous", "linkage_rate", "precision", "recall"]]

    attrition = feasibility["attrition"].copy()
    attrition = suppress_small_counts(attrition, ["input_children", "retained_children", "removed_children"], threshold=10)
    rule_summary = data["rule_summary"][["rule_id", "source", "category", "severity", "flagged_records", "status"]].copy()
    phenotype = data["phenotype_prevalence"][["phenotype", "version", "eligible_children", "flagged_children", "prevalence_among_eligible"]].copy()
    phenotype["prevalence_among_eligible"] = phenotype["prevalence_among_eligible"].map(_pct)
    release = data["release_diff"][["source", "previous_coverage", "current_coverage", "change", "qa_status"]].copy()

    warnings_html = "".join(f"<li>{warning}</li>" for warning in feasibility["warnings"])
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Synthetic Linked Child Data Portal V2</title>
<style>
:root{{--ink:#172033;--muted:#657087;--bg:#f4f6fb;--panel:#ffffff;--line:#e2e7f0;--nav:#17233f;--accent:#6c52d9;--warn:#fff5d8;--ok:#e8f7ef}}
*{{box-sizing:border-box}} body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--ink)}}
.app{{display:grid;grid-template-columns:238px 1fr;min-height:100vh}} .sidebar{{background:var(--nav);color:white;padding:24px 17px}}
.brand{{font-weight:700;font-size:18px;line-height:1.35;margin-bottom:22px}} .side-note{{font-size:12px;opacity:.78;line-height:1.45;margin-bottom:24px}}
.nav{{font-size:13px;padding:10px 9px;border-radius:8px;margin:3px 0;color:#dce4ff}} .nav.active{{background:#ffffff1d;color:white;font-weight:700}}
.main{{padding:28px 34px 48px;max-width:1500px}} h1{{font-size:27px;margin:0 0 4px}} h2{{font-size:19px;margin:28px 0 12px}} h3{{font-size:15px;margin:0 0 8px}}
.sub{{color:var(--muted);font-size:14px;margin-bottom:15px}} .banner{{background:var(--warn);border-left:5px solid #d49b00;padding:12px 14px;border-radius:6px;font-size:13px;line-height:1.45;margin:16px 0}}
.grid5{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}} .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px;box-shadow:0 2px 8px #27345108}} .metric{{font-size:26px;font-weight:700;margin-top:7px}} .label{{font-size:12px;color:var(--muted)}}
.data-table{{border-collapse:collapse;width:100%;background:white;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{padding:8px 9px;border-bottom:1px solid var(--line);text-align:left;font-size:12px;vertical-align:top}} th{{background:#eef1fb;font-weight:700}} tr:last-child td{{border-bottom:none}}
.warn-list{{font-size:13px;line-height:1.45;margin:0;padding-left:20px}} .pill{{display:inline-block;background:var(--ok);padding:4px 8px;border-radius:20px;font-size:12px;font-weight:700}}
.footer{{font-size:12px;color:var(--muted);margin-top:24px}}
</style></head>
<body><div class="app"><aside class="sidebar"><div class="brand">Synthetic Linked Child Data Research Support Portal</div><div class="side-note">Interactive Streamlit application<br>Static reviewer preview</div>
<div class="nav active">01 Resource overview</div><div class="nav">02 Variable catalogue</div><div class="nav">03 Data-quality audit</div><div class="nav">04 Linkage evaluation</div><div class="nav">05 Cohort feasibility</div><div class="nav">06 Attrition and manifest</div><div class="nav">07 Phenotype repository</div><div class="nav">08 Data refresh comparison</div>
</aside><main class="main"><h1>Synthetic linked child administrative-data portal</h1><div class="sub">Research feasibility, linkage-quality and governance-aware reporting prototype</div>
<div class="banner"><b>Synthetic demonstration only.</b> No ECHILD, HES, NPD or children's social-care records are used. Public portfolio mode displays aggregate outputs only. Non-zero cells below 10 are suppressed using an illustrative rule.</div>
<div class="grid5"><div class="card"><div class="label">Synthetic children</div><div class="metric">{len(children):,}</div></div><div class="card"><div class="label">Health episodes</div><div class="metric">{len(health):,}</div></div><div class="card"><div class="label">Education records</div><div class="metric">{len(education):,}</div></div><div class="card"><div class="label">Social-care events</div><div class="metric">{len(social):,}</div></div><div class="card"><div class="label">Quality flags</div><div class="metric">{len(issues):,}</div></div></div>
<div class="grid2"><section><h2>Linkage-quality evaluation</h2>{_table(linkage)}</section><section><h2>Feasibility warnings</h2><div class="card"><ul class="warn-list">{warnings_html}</ul></div><h2>Release comparison</h2>{_table(release)}</section></div>
<div class="grid2"><section><h2>Cohort attrition flow</h2>{_table(attrition)}</section><section><h2>Executable phenotype examples</h2>{_table(phenotype)}</section></div>
<h2>Quality-rule registry</h2>{_table(rule_summary)}
<div class="footer">Static preview of the dynamic Streamlit V2 portal. The live app provides filters, aggregate charts and downloadable synthetic feasibility reports.</div>
</main></div></body></html>"""
    (outputs / "dashboard_preview.html").write_text(html, encoding="utf-8")


def generate_reports(root: Path) -> None:
    processed = root / "data" / "processed"
    data = {
        "children": _read(processed / "children.csv", parse_dates=["birth_date"]),
        "health": _read(processed / "health_linked.csv", parse_dates=["admission_date", "discharge_date"]),
        "education": _read(processed / "education_linked.csv"),
        "social": _read(processed / "social_care_linked.csv", parse_dates=["referral_date"]),
        "issues": _read(processed / "quality_issues.csv"),
        "linkage_eval": _read(processed / "linkage_evaluation_summary.csv"),
        "linkage_by_deprivation": _read(processed / "linkage_by_deprivation.csv"),
        "rule_summary": _read(processed / "quality_rule_summary.csv"),
        "phenotype_prevalence": _read(processed / "phenotype_prevalence.csv"),
        "release_diff": _read(processed / "release_diff.csv"),
        "education_missingness": _read(processed / "education_missingness_by_year.csv"),
        "social_missingness": _read(processed / "social_missingness_by_region.csv"),
    }
    filters = CohortFilters(
        cohort_design="Index hospital-admission cohort",
        birth_year_min=2010,
        birth_year_max=2015,
        min_follow_up_years=2,
        index_year_min=2018,
        index_year_max=2022,
        diagnosis_group="Respiratory",
        require_health=True,
        require_education=True,
        require_social_care=False,
        outcome_phenotype="persistent_school_absence",
    )
    feasibility = build_cohort(
        data["children"],
        data["health"],
        data["education"],
        data["social"],
        filters,
        linkage_by_deprivation=data["linkage_by_deprivation"],
    )
    _write_markdown_reports(root, data, feasibility)
    _preview_html(root, data, feasibility)


if __name__ == "__main__":
    generate_reports(Path(__file__).resolve().parents[1])
