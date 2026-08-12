# Data Repository: Deep Learning Experiments

This repository contains the public evidence package for the datasets built to experiment with context-aware Deep Learning architectures on irregular clinical time series.

The underlying real dataset is derived from MIMIC-III. Because MIMIC-III is access-controlled, this repository intentionally includes only:

- aggregate metadata;
- model metrics and training histories;
- figures;
- methodology and data dictionaries;
- scripts and instructions to regenerate restricted CSV files from an authorized local MIMIC-III copy.

It does not publish row-level MIMIC-III derivatives with patient/admission identifiers, timestamps, clinical observations, or trained model weights.

## Repository layout

```text
Data_Repository/
  README.md
  requirements.txt
  data/
    public/
      metadata/
      metrics/
      synthetic/
    restricted/
      restricted_files_manifest.csv
  docs/
  figures/
  notebooks/
    mTAN-MIMIC.ipynb
  scripts/
    create_public_metadata.py
    generate_mimic_context_aware_subset.py
```

## Public data available for review

The public reviewable data is in:

- `data/public/metadata/sample_admissions_2000_summary.json`
- `data/public/metadata/split_summary.csv`
- `data/public/metadata/temporal_coverage_summary.csv`
- `data/public/metadata/dataset_schema.csv`
- `data/public/metadata/run_config_full_config.json`
- `data/public/metadata/run_config_full_light.json`
- `data/public/metrics/*.csv`
- `data/public/synthetic/*.csv`
- `data/public/synthetic/regenerated_full_package/*.csv`

These files summarize the available dataset and experiments without exposing restricted row-level records.

## Synthetic data available for review

Synthetic data generation was located outside `Experimentos`, in `Investigacion/Datasets/Data Simulation`. The available CSV files were copied to:

- `data/public/synthetic/simulated_sleep_data.csv`
- `data/public/synthetic/simulated_user_data.csv`

The original code also described a heart-rate event file that was not materialized in the source folder. A cleaned generator was added and used to create a complete reproducible package in:

- `data/public/synthetic/regenerated_full_package/simulated_sleep_data.csv`
- `data/public/synthetic/regenerated_full_package/simulated_heart_rate_data.csv`
- `data/public/synthetic/regenerated_full_package/simulated_user_data.csv`

See `docs/SYNTHETIC_DATA.md`.

## Restricted CSV files

The following CSV files are intentionally not included:

- `sample_admissions_2000.csv`
- `temporal_coverage_2000.csv`
- `temporal_events_2000.csv`

See `data/restricted/restricted_files_manifest.csv` for their purpose, local source path, public replacement, and generation step.

## Regenerating restricted CSV files

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Generate the admission cohort only:

```bash
python3 scripts/generate_mimic_context_aware_subset.py \
  --mimic-dir /path/to/MIMIC-III \
  --output-dir outputs/mimic_context_aware_subset
```

Generate the full temporal event file and coverage file:

```bash
python3 scripts/generate_mimic_context_aware_subset.py \
  --mimic-dir /path/to/MIMIC-III \
  --output-dir outputs/mimic_context_aware_subset \
  --run-full-extraction
```

After generating restricted files locally, update the public aggregate metadata:

```bash
python3 scripts/create_public_metadata.py \
  --source-dir outputs/mimic_context_aware_subset \
  --repository-dir .
```

## Dataset summary

The real dataset, `mimic_context_aware_subset`, contains a reproducible sample of 2,000 MIMIC-III admissions with:

- in-hospital mortality label;
- admission/patient context;
- 168-hour observation window from admission;
- irregular heart rate observations from `CHARTEVENTS`;
- irregular glucose observations from `LABEVENTS`;
- train/validation/test splits assigned by `subject_id`.

Synthetic sleep/user datasets were found in the broader project workspace and added to this repository. The heart-rate synthetic dataset can be regenerated with `scripts/generate_synthetic_sleep_hr.py` and is included in `data/public/synthetic/regenerated_full_package`.
