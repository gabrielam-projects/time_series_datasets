#!/usr/bin/env python3
"""Create public aggregate metadata from local restricted MIMIC-III derivatives."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_public_metadata(source_dir: Path, repository_dir: Path) -> None:
    public_metadata = repository_dir / "data" / "public" / "metadata"
    restricted_dir = repository_dir / "data" / "restricted"
    public_metadata.mkdir(parents=True, exist_ok=True)
    restricted_dir.mkdir(parents=True, exist_ok=True)

    admissions_path = source_dir / "sample_admissions_2000.csv"
    coverage_path = source_dir / "temporal_coverage_2000.csv"

    if admissions_path.exists():
        admissions = pd.read_csv(admissions_path)
        split_summary = (
            admissions.groupby("split")
            .agg(
                admissions=("hadm_id", "size"),
                subjects=("subject_id", "nunique"),
                mortality_rate=("mortality_label", "mean"),
                age_mean=("age", "mean"),
                age_std=("age", "std"),
            )
            .reindex(["train", "val", "test"])
            .round(6)
        )
        split_summary.to_csv(public_metadata / "split_summary.csv")

    if coverage_path.exists():
        coverage = pd.read_csv(coverage_path)
        rows = []
        for column in [c for c in ["heart_rate", "glucose"] if c in coverage.columns]:
            values = coverage[column]
            rows.append(
                {
                    "variable": column,
                    "total_events": int(values.sum()),
                    "admissions_with_observation": int((values > 0).sum()),
                    "admissions_without_observation": int((values == 0).sum()),
                    "mean_observations_per_admission": round(float(values.mean()), 6),
                    "std_observations_per_admission": round(float(values.std()), 6),
                    "min_observations_per_admission": int(values.min()),
                    "p25_observations_per_admission": round(float(values.quantile(0.25)), 6),
                    "median_observations_per_admission": round(float(values.median()), 6),
                    "p75_observations_per_admission": round(float(values.quantile(0.75)), 6),
                    "max_observations_per_admission": int(values.max()),
                }
            )
        pd.DataFrame(rows).to_csv(public_metadata / "temporal_coverage_summary.csv", index=False)

    schema_rows = [
        ("sample_admissions_2000.csv", "subject_id", "MIMIC-III patient identifier; restricted"),
        ("sample_admissions_2000.csv", "hadm_id", "MIMIC-III admission identifier; restricted"),
        ("sample_admissions_2000.csv", "admit_time", "Admission timestamp; restricted"),
        ("sample_admissions_2000.csv", "discharge_time", "Discharge timestamp; restricted"),
        ("sample_admissions_2000.csv", "death_time", "Death timestamp when available; restricted"),
        ("sample_admissions_2000.csv", "window_start", "Start of 168-hour extraction window"),
        ("sample_admissions_2000.csv", "window_end", "End of 168-hour extraction window"),
        ("sample_admissions_2000.csv", "mortality_label", "Binary in-hospital mortality label"),
        ("sample_admissions_2000.csv", "age", "Age at admission; ages greater than 120 grouped as 90"),
        ("sample_admissions_2000.csv", "gender", "Patient gender category"),
        ("sample_admissions_2000.csv", "insurance", "Admission insurance category"),
        ("sample_admissions_2000.csv", "admission_type", "Admission type category"),
        ("sample_admissions_2000.csv", "admission_location", "Admission location category"),
        ("sample_admissions_2000.csv", "ethnicity", "Ethnicity category"),
        ("sample_admissions_2000.csv", "split", "Train/validation/test split assigned by subject_id"),
        ("temporal_events_2000.csv", "variable", "Temporal variable: heart_rate or glucose"),
        ("temporal_events_2000.csv", "source", "MIMIC-III source table: CHARTEVENTS or LABEVENTS"),
        ("temporal_events_2000.csv", "itemid", "MIMIC-III item identifier"),
        ("temporal_events_2000.csv", "chart_time", "Event timestamp; restricted"),
        ("temporal_events_2000.csv", "hours_since_admit", "Relative time in hours since admission"),
        ("temporal_events_2000.csv", "value", "Observed numeric clinical value"),
        ("temporal_events_2000.csv", "mask", "Observation mask"),
    ]
    pd.DataFrame(schema_rows, columns=["file", "column", "description"]).to_csv(
        public_metadata / "dataset_schema.csv", index=False
    )

    manifest = pd.DataFrame(
        [
            {
                "file": "sample_admissions_2000.csv",
                "local_source": str(admissions_path),
                "status": "excluded from public repository",
                "reason": "row-level MIMIC-III derivative with identifiers, timestamps and labels",
                "public_replacement": "data/public/metadata/sample_admissions_2000_summary.json; data/public/metadata/split_summary.csv",
                "generation_step": "Run scripts/generate_mimic_context_aware_subset.py",
            },
            {
                "file": "temporal_coverage_2000.csv",
                "local_source": str(coverage_path),
                "status": "excluded from public repository",
                "reason": "per-admission coverage keyed by hadm_id",
                "public_replacement": "data/public/metadata/temporal_coverage_summary.csv",
                "generation_step": "Run full temporal extraction",
            },
            {
                "file": "temporal_events_2000.csv",
                "local_source": str(source_dir / "temporal_events_2000.csv"),
                "status": "restricted; regenerate from source MIMIC-III CSV files",
                "reason": "row-level MIMIC-III derivative with identifiers, timestamps and clinical values",
                "public_replacement": "data/public/metadata/temporal_coverage_summary.csv",
                "generation_step": "Run scripts/generate_mimic_context_aware_subset.py --run-full-extraction",
            },
        ]
    )
    manifest.to_csv(restricted_dir / "restricted_files_manifest.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--repository-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    build_public_metadata(args.source_dir, args.repository_dir)


if __name__ == "__main__":
    main()

