# User guide

## Rebuild synthetic outputs

```bash
python run_pipeline.py --n-children 5000
```

Use a smaller value such as `1500` for quick automated tests. Use a larger value such as `100000` for a local scalability check when memory allows.

## Launch the interactive portal

```bash
streamlit run app.py
```

## Suggested review path

Open the linkage-quality page first and review variation across deprivation quintiles. Then use the cohort-feasibility builder to define a cohort and download the aggregate feasibility outputs. The phenotype and refresh pages show how definitions and releases are documented.

## Public-output limits

The public app does not display child-level records. It uses an illustrative small-cell suppression threshold stored in `config/disclosure_rules.yml`.
