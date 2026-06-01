"""Dynamic Streamlit portal for a synthetic linked child-data resource."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

from src.build_cohort import CohortFilters, build_cohort, render_feasibility_report, render_manifest_yaml
from src.disclosure_control import load_disclosure_rules, public_mode_banner, suppress_small_counts

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
CONFIG = ROOT / "config"

st.set_page_config(
    page_title="Synthetic Linked Child Data Portal V2",
    page_icon="📊",
    layout="wide",
)


def ensure_generated_data() -> None:
    required = DATA / "children.csv"
    if required.exists():
        return
    from run_pipeline import run_pipeline

    with st.spinner("Generating fully synthetic demonstration records..."):
        run_pipeline(repo_root=ROOT, n_children=5_000)


@st.cache_data
def load_data() -> dict[str, pd.DataFrame]:
    ensure_generated_data()
    return {
        "children": pd.read_csv(DATA / "children.csv", parse_dates=["birth_date"]),
        "health": pd.read_csv(DATA / "health_linked.csv", parse_dates=["admission_date", "discharge_date"]),
        "education": pd.read_csv(DATA / "education_linked.csv"),
        "social": pd.read_csv(DATA / "social_care_linked.csv", parse_dates=["referral_date"]),
        "issues": pd.read_csv(DATA / "quality_issues.csv"),
        "metrics": pd.read_csv(DATA / "variable_quality_metrics.csv"),
        "catalogue": pd.read_csv(DATA / "metadata_catalogue.csv"),
        "rule_summary": pd.read_csv(DATA / "quality_rule_summary.csv"),
        "linkage": pd.read_csv(DATA / "linkage_table.csv"),
        "linkage_eval": pd.read_csv(DATA / "linkage_evaluation_summary.csv"),
        "linkage_by_deprivation": pd.read_csv(DATA / "linkage_by_deprivation.csv"),
        "linkage_by_region": pd.read_csv(DATA / "linkage_by_region.csv"),
        "linkage_by_confidence": pd.read_csv(DATA / "linkage_by_confidence.csv"),
        "refresh": pd.read_csv(DATA / "data_refresh_log.csv"),
        "release_diff": pd.read_csv(DATA / "release_diff.csv"),
        "source_trends": pd.read_csv(DATA / "data_source_trends.csv"),
        "education_missingness": pd.read_csv(DATA / "education_missingness_by_year.csv"),
        "social_missingness": pd.read_csv(DATA / "social_missingness_by_region.csv"),
        "phenotype_prevalence": pd.read_csv(DATA / "phenotype_prevalence.csv"),
    }


def percent(value: float) -> str:
    return f"{100 * float(value):.1f}%"


def show_governance_banner(threshold: int) -> None:
    st.warning(
        "Synthetic demonstration only. No ECHILD, HES, NPD or children's social-care records are used.\n\n"
        + public_mode_banner(threshold)
    )


def overview_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("01 · Research-resource overview")
    st.caption("Aggregate monitoring for a fully synthetic linked child administrative-data resource.")
    columns = st.columns(5)
    columns[0].metric("Synthetic children", f"{len(data['children']):,}")
    columns[1].metric("Health episodes", f"{len(data['health']):,}")
    columns[2].metric("Education records", f"{len(data['education']):,}")
    columns[3].metric("Social-care events", f"{len(data['social']):,}")
    columns[4].metric("Quality flags", f"{len(data['issues']):,}")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Record volume by source and year")
        fig = px.line(
            data["source_trends"],
            x="year",
            y="records",
            color="source",
            markers=True,
            labels={"records": "Synthetic records", "year": "Year"},
        )
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Current release manifest")
        st.dataframe(data["refresh"], width="stretch", hide_index=True)

    st.subheader("Current resource warnings")
    st.warning("Education attendance completeness is lower during academic year 2020.")
    st.warning("Social-care assessment-outcome missingness differs across regions.")
    st.warning("Linkage rates vary across deprivation quintiles; downstream subgroup comparisons require a linkage-bias check.")


def catalogue_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("02 · Variable catalogue")
    st.caption("Filter metadata, coverage years, provenance, caveats and recommended use.")
    catalogue = data["catalogue"].copy()
    col1, col2, col3 = st.columns(3)
    with col1:
        sources = st.multiselect("Source", sorted(catalogue["source"].unique()), default=sorted(catalogue["source"].unique()))
    with col2:
        modules = st.multiselect("Module", sorted(catalogue["module"].unique()), default=sorted(catalogue["module"].unique()))
    with col3:
        minimum_completeness = st.slider("Minimum observed completeness", 0.0, 1.0, 0.0, 0.05)
    display = catalogue[catalogue["source"].isin(sources) & catalogue["module"].isin(modules)].copy()
    display = display[display["completeness_rate"].fillna(1.0) >= minimum_completeness]
    st.dataframe(display, width="stretch", hide_index=True)

    selected = st.selectbox("Inspect one variable", display["variable_name"].tolist() if len(display) else ["No matching variable"])
    if len(display):
        row = display.loc[display["variable_name"].eq(selected)].iloc[0]
        st.info(
            f"**{row['variable_name']}** · {row['description']}\n\n"
            f"**Coverage:** {row['available_from']}–{row['available_to']}  \n"
            f"**Known caveat:** {row['known_caveat']}  \n"
            f"**Recommended use:** {row['recommended_use']}  \n"
            f"**Provenance:** {row['provenance']}"
        )


def quality_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("03 · Data-quality audit")
    st.caption("Config-driven checks covering completeness, validity, consistency and duplication.")
    rules = data["rule_summary"].copy()
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_sources = st.multiselect("Source", sorted(rules["source"].unique()), default=sorted(rules["source"].unique()))
    with col2:
        selected_categories = st.multiselect("Rule category", sorted(rules["category"].unique()), default=sorted(rules["category"].unique()))
    with col3:
        selected_severity = st.multiselect("Severity", sorted(rules["severity"].unique()), default=sorted(rules["severity"].unique()))
    filtered = rules[
        rules["source"].isin(selected_sources)
        & rules["category"].isin(selected_categories)
        & rules["severity"].isin(selected_severity)
    ]
    st.dataframe(filtered, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        fig = px.line(
            data["education_missingness"],
            x="academic_year",
            y="attendance_missing_rate",
            markers=True,
            labels={"attendance_missing_rate": "Missing rate", "academic_year": "Academic year"},
            title="Attendance missingness by academic year",
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = px.bar(
            data["social_missingness"].sort_values("assessment_outcome_missing_rate", ascending=False),
            x="local_authority_region",
            y="assessment_outcome_missing_rate",
            labels={"assessment_outcome_missing_rate": "Missing rate", "local_authority_region": "Region"},
            title="Social-care assessment-outcome missingness by region",
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, width="stretch")

    st.info("Record-level quality flags are generated internally for quality assurance, but row-level records are not displayed in public portfolio mode.")


def linkage_page(data: dict[str, pd.DataFrame], threshold: int) -> None:
    st.header("04 · Linkage-quality evaluation")
    st.caption("Source-level accuracy metrics and subgroup linkage-rate checks using synthetic internal truth.")
    source_summary = data["linkage_eval"].copy()
    display_summary = source_summary.copy()
    for column in ["linkage_rate", "precision", "recall", "false_link_rate"]:
        display_summary[column] = display_summary[column].map(percent)
    st.dataframe(
        suppress_small_counts(display_summary, ["records", "matched", "correct_links", "false_links", "missed_links", "ambiguous", "unmatched"], threshold),
        width="stretch",
        hide_index=True,
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        source = st.selectbox("Source", sorted(data["linkage_by_deprivation"]["source"].unique()), index=0)
        stratify = st.radio("Stratify linkage rate by", ["Deprivation quintile", "Region", "Confidence band"])
    with col2:
        if stratify == "Deprivation quintile":
            subgroup = data["linkage_by_deprivation"].query("source == @source").copy()
            x = "deprivation_quintile"
        elif stratify == "Region":
            subgroup = data["linkage_by_region"].query("source == @source").copy()
            x = "region"
        else:
            subgroup = data["linkage_by_confidence"].query("source == @source").copy()
            x = "confidence_band"
        fig = px.bar(subgroup, x=x, y="linkage_rate", labels={"linkage_rate": "Linkage rate"}, title=f"{source}: linkage rate by {stratify.lower()}")
        fig.update_yaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(fig, width="stretch")
        subgroup_display = subgroup.copy()
        for column in ["linkage_rate", "precision", "recall", "false_link_rate"]:
            subgroup_display[column] = subgroup_display[column].map(percent)
        st.dataframe(
            suppress_small_counts(subgroup_display, ["records", "matched", "correct_links", "false_links", "missed_links", "ambiguous", "unmatched"], threshold),
            width="stretch",
            hide_index=True,
        )

    education = data["linkage_by_deprivation"].query("source == 'education'")
    if len(education) and education["linkage_rate"].max() - education["linkage_rate"].min() > 0.02:
        st.warning("Potential linkage-bias warning: education linkage rates differ across deprivation quintiles. Compare linked and unlinked groups before interpreting downstream subgroup differences.")


def build_interactive_cohort(data: dict[str, pd.DataFrame]) -> dict:
    children = data["children"]
    st.subheader("Define the research question")
    question = st.text_input("Research question", "Persistent school absence after respiratory hospital admission")
    cohort_design = st.radio("Cohort design", ["Index hospital-admission cohort", "School inception cohort", "Birth cohort"], horizontal=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        birth_year_range = st.slider(
            "Birth-year range",
            int(children["birth_date"].dt.year.min()),
            int(children["birth_date"].dt.year.max()),
            (2010, 2015),
        )
        follow_up = st.slider("Minimum potential follow-up years", 0, 15, 2)
        regions = st.multiselect("Regions", sorted(children["region"].unique()))
    with col2:
        deprivation = st.multiselect("Deprivation quintiles", [1, 2, 3, 4, 5])
        index_range = st.slider("Index-admission year range", 2016, 2025, (2018, 2022))
        school_inception_year = st.slider("School-inception academic year", 2017, 2025, 2020)
        diagnoses = [None] + sorted(data["health"]["diagnosis_group"].dropna().astype(str).unique().tolist())
        diagnosis = st.selectbox("Optional diagnosis group", diagnoses, index=diagnoses.index("Respiratory") if "Respiratory" in diagnoses else 0)
    with col3:
        require_health = st.checkbox("Require linked health module", value=True)
        require_education = st.checkbox("Require linked education module", value=True)
        require_social = st.checkbox("Require linked social-care module", value=False)
        outcome = st.selectbox("Outcome phenotype", ["persistent_school_absence"])

    filters = CohortFilters(
        cohort_design=cohort_design,
        birth_year_min=birth_year_range[0],
        birth_year_max=birth_year_range[1],
        regions=tuple(regions),
        deprivation_quintiles=tuple(int(value) for value in deprivation),
        min_follow_up_years=follow_up,
        index_year_min=index_range[0],
        index_year_max=index_range[1],
        school_inception_year=school_inception_year,
        diagnosis_group=diagnosis,
        require_health=require_health,
        require_education=require_education,
        require_social_care=require_social,
        outcome_phenotype=outcome,
    )
    result = build_cohort(
        data["children"],
        data["health"],
        data["education"],
        data["social"],
        filters,
        linkage_by_deprivation=data["linkage_by_deprivation"],
    )
    result["manifest"]["research_question"] = question
    st.session_state["latest_cohort_result"] = result
    return result


def cohort_page(data: dict[str, pd.DataFrame], threshold: int) -> None:
    st.header("05 · Cohort feasibility builder")
    st.caption("Scope a research question, construct a cohort spine and generate an aggregate feasibility report.")
    result = build_interactive_cohort(data)
    summary = result["summary"]
    metrics = st.columns(5)
    metrics[0].metric("Initial spine", f"{summary['initial_population_spine']:,}")
    metrics[1].metric("Final cohort", f"{summary['final_analytical_cohort']:,}")
    metrics[2].metric("Health records", f"{summary['health_records']:,}")
    metrics[3].metric("Education records", f"{summary['education_records']:,}")
    metrics[4].metric("Median follow-up", f"{summary['median_follow_up_years']:.1f} years")

    for warning in result["warnings"]:
        st.warning(warning)
    st.subheader("Aggregate cohort attrition")
    st.dataframe(
        suppress_small_counts(result["attrition"], ["input_children", "retained_children", "removed_children"], threshold),
        width="stretch",
        hide_index=True,
    )
    st.info("Restricted in public portfolio mode: child-level records and row-level extracts are not displayed or downloadable.")

    col1, col2, col3 = st.columns(3)
    col1.download_button("Download feasibility report", render_feasibility_report(result), file_name="feasibility_report.md", mime="text/markdown")
    col2.download_button("Download attrition CSV", result["attrition"].to_csv(index=False), file_name="cohort_attrition.csv", mime="text/csv")
    col3.download_button("Download extract manifest", render_manifest_yaml(result), file_name="extract_manifest.yml", mime="text/yaml")


def attrition_page(data: dict[str, pd.DataFrame], threshold: int) -> None:
    st.header("06 · Attrition flow and extract manifest")
    st.caption("Reviewer-facing aggregate outputs for cohort-scoping discussions.")
    result = st.session_state.get("latest_cohort_result")
    if result is None:
        result = build_cohort(
            data["children"],
            data["health"],
            data["education"],
            data["social"],
            CohortFilters(),
            linkage_by_deprivation=data["linkage_by_deprivation"],
        )
    st.subheader("Cohort attrition flow")
    display = suppress_small_counts(result["attrition"], ["input_children", "retained_children", "removed_children"], threshold)
    st.dataframe(display, width="stretch", hide_index=True)
    st.subheader("Extract manifest")
    st.code(render_manifest_yaml(result), language="yaml")
    st.info("The manifest lists required sources and variables. It does not expose child-level identifiers or a row-level extract.")


def phenotype_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("07 · Executable phenotype repository examples")
    st.caption("Versioned synthetic definitions with executable prevalence summaries.")
    prevalence = data["phenotype_prevalence"].copy()
    prevalence["prevalence_among_eligible"] = prevalence["prevalence_among_eligible"].map(percent)
    prevalence["coverage_of_spine"] = prevalence["coverage_of_spine"].map(percent)
    st.dataframe(prevalence, width="stretch", hide_index=True)

    with (CONFIG / "phenotypes.yml").open("r", encoding="utf-8") as handle:
        definitions = yaml.safe_load(handle)
    selected = st.selectbox("Inspect one phenotype definition", list(definitions))
    st.code(yaml.safe_dump({selected: definitions[selected]}, sort_keys=False, allow_unicode=True), language="yaml")
    st.info("These examples use simplified synthetic variables. They are not clinical code lists.")


def refresh_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("08 · Data refresh and release comparison")
    st.caption("Check expected sources, modules, coverage years and quality-assurance status before extract creation.")
    st.dataframe(data["release_diff"], width="stretch", hide_index=True)
    warnings = data["release_diff"][data["release_diff"]["qa_status"].ne("Passed")]
    if len(warnings):
        st.warning("One or more refreshed sources require review before release sign-off.")
    st.info("A production workflow would document data-owner transfers, variable-level changes, quality checks and release approval inside the approved environment.")


def aggregate_sql_page() -> None:
    st.header("09 · Safe aggregate SQL examples")
    st.caption("Predefined read-only examples only. Free-text SQL is disabled in public portfolio mode.")
    examples = {
        "Attendance missingness by year": """SELECT academic_year, ROUND(100.0 * AVG(CASE WHEN attendance_rate IS NULL THEN 1 ELSE 0 END), 1) AS missing_percent\nFROM education_records\nGROUP BY academic_year\nORDER BY academic_year;""",
        "Health episodes by diagnosis group": """SELECT diagnosis_group, COUNT(*) AS episodes\nFROM health_episodes\nGROUP BY diagnosis_group\nORDER BY episodes DESC;""",
        "Linkage evaluation summary": """SELECT source, records, matched, correct_links, false_links, ambiguous, linkage_rate, precision, recall\nFROM linkage_evaluation_summary\nORDER BY source;""",
        "Phenotype prevalence": """SELECT phenotype, version, eligible_children, flagged_children, prevalence_among_eligible\nFROM phenotype_prevalence\nORDER BY phenotype;""",
    }
    selected = st.selectbox("Aggregate query", list(examples))
    st.code(examples[selected], language="sql")
    if st.button("Run predefined aggregate query"):
        import sqlite3

        with sqlite3.connect(DATA / "synthetic_echild.db") as connection:
            result = pd.read_sql_query(examples[selected], connection)
        st.dataframe(result, width="stretch", hide_index=True)
    st.info("Restricted in public portfolio mode: row-level query access is disabled.")


def main() -> None:
    data = load_data()
    rules = load_disclosure_rules(CONFIG / "disclosure_rules.yml")
    threshold = int(rules.get("minimum_cell_count", 10))

    st.title("Synthetic Linked Child Administrative-Data Research Support Portal")
    show_governance_banner(threshold)
    st.sidebar.title("V2 navigation")
    page = st.sidebar.radio(
        "Page",
        [
            "01 Resource overview",
            "02 Variable catalogue",
            "03 Data-quality audit",
            "04 Linkage-quality evaluation",
            "05 Cohort feasibility builder",
            "06 Attrition flow and extract manifest",
            "07 Phenotype repository",
            "08 Data refresh comparison",
            "09 Safe aggregate SQL examples",
        ],
    )
    st.sidebar.caption("Dynamic Streamlit interface\n\nSynthetic records only")

    if page == "01 Resource overview":
        overview_page(data)
    elif page == "02 Variable catalogue":
        catalogue_page(data)
    elif page == "03 Data-quality audit":
        quality_page(data)
    elif page == "04 Linkage-quality evaluation":
        linkage_page(data, threshold)
    elif page == "05 Cohort feasibility builder":
        cohort_page(data, threshold)
    elif page == "06 Attrition flow and extract manifest":
        attrition_page(data, threshold)
    elif page == "07 Phenotype repository":
        phenotype_page(data)
    elif page == "08 Data refresh comparison":
        refresh_page(data)
    else:
        aggregate_sql_page()


if __name__ == "__main__":
    main()
