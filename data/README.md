# Data Package

## Public

`data/public` contains aggregate files that can be reviewed in a public GitHub repository:

- `metadata/`: dataset summaries, schema, split statistics, coverage statistics and run configurations.
- `metrics/`: experiment summaries and training histories for P1, P2 and P3.
- `synthetic/`: synthetic sleep, heart-rate and user-demographic CSV files.

## Restricted

`data/restricted` contains only a manifest. It does not contain restricted row-level data.

Restricted row-level CSV files must be regenerated from an authorized MIMIC-III copy using `scripts/generate_mimic_context_aware_subset.py`.
