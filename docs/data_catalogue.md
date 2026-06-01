# Data catalogue note

The dynamic variable catalogue is generated from `src/process_data.py` and written to:

```text
data/processed/metadata_catalogue.csv
```

Each catalogue row records:

- source and module;
- variable name and description;
- data type;
- coverage years;
- known caveat;
- provenance;
- recommended use;
- observed missingness and completeness where available.

The catalogue is part of the synthetic demonstration and should not be interpreted as documentation for ECHILD, HES, NPD or children's social-care records.
