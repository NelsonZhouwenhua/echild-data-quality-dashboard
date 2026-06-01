# Public portal and trusted research environment boundary

## Public portfolio mode

The deployed demonstration exposes:

- aggregate source counts and trends;
- metadata catalogue entries;
- aggregate data-quality summaries;
- source-level and subgroup linkage metrics;
- aggregate cohort attrition;
- feasibility warnings;
- versioned synthetic phenotype definitions;
- release-comparison outputs;
- predefined aggregate SQL examples.

It does not expose:

- child-level records;
- source-person identifiers;
- arbitrary SQL queries;
- row-level extracts;
- internal synthetic linkage-truth tables.

## Production TRE mode

In a production setting, approved analysts would carry out row-level processing inside the trusted research environment (TRE). Only checked outputs would leave that environment. The public app illustrates the separation between internal analysis and external reporting; it is not an implementation of any specific TRE.
