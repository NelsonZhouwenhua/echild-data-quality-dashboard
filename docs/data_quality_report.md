# Synthetic data-quality audit report

> Synthetic demonstration only. The rules are illustrative and should be adapted to the approved data environment and research question.

## Quality-rule registry summary

| rule_id                                  | source      | category     | severity   | check_name                                    |   flagged_records | status   | recommended_action                                                         |
|:-----------------------------------------|:------------|:-------------|:-----------|:----------------------------------------------|------------------:|:---------|:---------------------------------------------------------------------------|
| education_attendance_out_of_range        | education   | validity     | error      | attendance_out_of_range                       |               380 | Review   | Set invalid values to missing and document the cleaning rule.              |
| health_admission_before_birth            | health      | consistency  | error      | admission_before_birth                        |                50 | Review   | Exclude flagged records from analysis and review the source logic.         |
| health_discharge_before_admission        | health      | consistency  | error      | discharge_before_admission                    |                36 | Review   | Exclude flagged records and review event-date derivation.                  |
| social_care_referral_before_birth        | social_care | consistency  | error      | referral_before_birth                         |                11 | Review   | Exclude flagged records and review event-date derivation.                  |
| education_school_stage_age_inconsistency | education   | consistency  | warning    | school_stage_age_inconsistency                |               858 | Review   | Review age and school-stage logic before cohort extraction.                |
| duplicate_source_record_id               | all         | duplication  | warning    | duplicate_source_record_id                    |               746 | Review   | Apply a documented deduplication rule and retain an audit count.           |
| education_attendance_missingness_shift   | education   | completeness | warning    | attendance_missingness_shift_2020             |                 1 | Review   | Report the 2020 limitation and run a sensitivity analysis excluding 2020.  |
| social_care_assessment_missingness_shift | social_care | completeness | warning    | assessment_outcome_regional_missingness_shift |                 1 | Review   | Report regional variation and check whether subgroup results are affected. |

## Attendance missingness by academic year

|   academic_year |   attendance_missing_rate |
|----------------:|--------------------------:|
|            2017 |                 0.0320648 |
|            2018 |                 0.0356186 |
|            2019 |                 0.0324262 |
|            2020 |                 0.219671  |
|            2021 |                 0.0358638 |
|            2022 |                 0.036254  |
|            2023 |                 0.0356847 |
|            2024 |                 0.0332556 |
|            2025 |                 0.0367525 |

## Social-care assessment-outcome missingness by region

| local_authority_region   |   assessment_outcome_missing_rate |
|:-------------------------|----------------------------------:|
| East Midlands            |                         0.0987342 |
| London                   |                         0.0913706 |
| North East               |                         0.262873  |
| North West               |                         0.0902778 |
| South East               |                         0.0661578 |
| South West               |                         0.0648379 |
| West Midlands            |                         0.22293   |
| Yorkshire and The Humber |                         0.06621   |
