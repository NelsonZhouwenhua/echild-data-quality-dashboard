# Synthetic linked child-data feasibility report

> Synthetic demonstration only. No restricted administrative records are used.

## Aggregate cohort summary

- Initial population spine: 5,000
- Final analytical cohort: 648
- Health records in scope: 2,092
- Education records in scope: 12,984
- Social-care records in scope: 409
- Median potential follow-up: 12.0 years

## Cohort attrition

| step                       | description                                                  |   input_children |   retained_children |   removed_children |
|:---------------------------|:-------------------------------------------------------------|-----------------:|--------------------:|-------------------:|
| Population spine           | All synthetic children                                       |             5000 |                5000 |                  0 |
| Birth-year eligibility     | Born between 2010 and 2015                                   |             5000 |                2778 |               2222 |
| Follow-up eligibility      | At least 2 years of potential follow-up                      |             2778 |                2778 |                  0 |
| Index admission            | First Respiratory admission during 2018-2022                 |             2778 |                 648 |               2130 |
| Linked education module    | At least one matched education record                        |              648 |                 648 |                  0 |
| Valid outcome availability | Sufficient valid records to derive persistent_school_absence |              648 |                 648 |                  0 |

## Feasibility warnings

- Attendance completeness is lower during academic year 2020. Consider a sensitivity analysis excluding 2020.
- Education linkage rates differ across deprivation quintiles. Compare linked and unlinked groups before interpreting subgroup results.
- This is a descriptive feasibility assessment using synthetic data. It is not a causal-effect estimate.

## Governance note

This public portfolio report contains aggregate synthetic outputs only. A row-level extract would remain inside an approved trusted research environment.
