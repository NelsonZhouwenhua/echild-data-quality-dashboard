# Synthetic data-refresh comparison

> Synthetic demonstration only.

| source      |   previous_release |   current_release | previous_coverage   | current_coverage   | previous_modules                   | current_modules                    | change                          | qa_status   |
|:------------|-------------------:|------------------:|:--------------------|:-------------------|:-----------------------------------|:-----------------------------------|:--------------------------------|:------------|
| education   |            2025_01 |           2026_01 | 2017-2024           | 2017-2025          | attendance, enrolment, sen_support | attendance, enrolment, sen_support | coverage 2017-2024 -> 2017-2025 | Warning     |
| health      |            2025_01 |           2026_01 | 2016-2024           | 2016-2025          | admissions, outpatient             | admissions, outpatient             | coverage 2016-2024 -> 2016-2025 | Passed      |
| social_care |            2025_01 |           2026_01 | 2016-2024           | 2016-2025          | assessments, referrals             | assessments, referrals             | coverage 2016-2024 -> 2016-2025 | Warning     |

## Review note

A refresh workflow should confirm that expected modules, variables and years are present before a new release is used for research extracts.
