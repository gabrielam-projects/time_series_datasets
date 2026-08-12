#!/usr/bin/env python3
"""Generate the restricted MIMIC-III-derived CSV files for the experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


HEART_RATE_ITEMIDS = [211, 220045]
GLUCOSE_LABITEMIDS = [50809, 50931]
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}


def compute_mimic_age(admit_time: pd.Series, dob: pd.Series) -> pd.Series:
    birthday_passed = (
        (admit_time.dt.month > dob.dt.month)
        | (admit_time.dt.month.eq(dob.dt.month) & admit_time.dt.day.ge(dob.dt.day))
    )
    age = (admit_time.dt.year - dob.dt.year - (~birthday_passed).astype(int)).astype(float)
    age = age.mask(age.gt(120), 90)
    return age.clip(lower=0)


def assign_subject_splits(sample: pd.DataFrame, random_seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    subject_ids = sample["subject_id"].drop_duplicates().to_numpy()
    rng.shuffle(subject_ids)

    n_subjects = len(subject_ids)
    n_train = int(round(n_subjects * SPLIT_FRACTIONS["train"]))
    n_val = int(round(n_subjects * SPLIT_FRACTIONS["val"]))

    split_map = {}
    for subject_id in subject_ids[:n_train]:
        split_map[int(subject_id)] = "train"
    for subject_id in subject_ids[n_train : n_train + n_val]:
        split_map[int(subject_id)] = "val"
    for subject_id in subject_ids[n_train + n_val :]:
        split_map[int(subject_id)] = "test"

    sample = sample.copy()
    sample["split"] = sample["subject_id"].map(split_map)
    return sample


def build_sample_admissions(
    mimic_dir: Path,
    output_dir: Path,
    n_samples: int,
    random_seed: int,
    window_hours: int,
) -> pd.DataFrame:
    admissions_path = mimic_dir / "ADMISSIONS.csv"
    patients_path = mimic_dir / "PATIENTS.csv"

    admission_cols = [
        "SUBJECT_ID",
        "HADM_ID",
        "ADMITTIME",
        "DISCHTIME",
        "DEATHTIME",
        "ADMISSION_TYPE",
        "ADMISSION_LOCATION",
        "INSURANCE",
        "ETHNICITY",
        "HOSPITAL_EXPIRE_FLAG",
        "HAS_CHARTEVENTS_DATA",
    ]
    patient_cols = ["SUBJECT_ID", "GENDER", "DOB"]

    admissions = pd.read_csv(
        admissions_path,
        usecols=admission_cols,
        parse_dates=["ADMITTIME", "DISCHTIME", "DEATHTIME"],
    )
    patients = pd.read_csv(patients_path, usecols=patient_cols, parse_dates=["DOB"])

    cohort = admissions.loc[admissions["HAS_CHARTEVENTS_DATA"].eq(1)].merge(
        patients, on="SUBJECT_ID", how="left", validate="many_to_one"
    )
    cohort["AGE"] = compute_mimic_age(cohort["ADMITTIME"], cohort["DOB"])
    cohort["WINDOW_START"] = cohort["ADMITTIME"]
    cohort["WINDOW_END"] = cohort["WINDOW_START"] + pd.to_timedelta(window_hours, unit="h")
    cohort = cohort.rename(
        columns={
            "SUBJECT_ID": "subject_id",
            "HADM_ID": "hadm_id",
            "HOSPITAL_EXPIRE_FLAG": "mortality_label",
            "GENDER": "gender",
            "AGE": "age",
            "INSURANCE": "insurance",
            "ADMISSION_TYPE": "admission_type",
            "ADMISSION_LOCATION": "admission_location",
            "ETHNICITY": "ethnicity",
            "ADMITTIME": "admit_time",
            "DISCHTIME": "discharge_time",
            "DEATHTIME": "death_time",
            "WINDOW_START": "window_start",
            "WINDOW_END": "window_end",
        }
    )

    context_cols = [
        "subject_id",
        "hadm_id",
        "admit_time",
        "discharge_time",
        "death_time",
        "window_start",
        "window_end",
        "mortality_label",
        "age",
        "gender",
        "insurance",
        "admission_type",
        "admission_location",
        "ethnicity",
    ]
    cohort = cohort[context_cols].drop_duplicates(subset=["subject_id", "hadm_id"])

    if len(cohort) < n_samples:
        raise ValueError(f"Base cohort has {len(cohort)} admissions; {n_samples} requested.")

    sample = (
        cohort.sample(n=n_samples, random_state=random_seed)
        .sort_values(["subject_id", "hadm_id"])
        .reset_index(drop=True)
    )
    sample = assign_subject_splits(sample, random_seed)

    assert sample[["subject_id", "hadm_id"]].duplicated().sum() == 0
    assert sample["mortality_label"].isin([0, 1]).all()
    assert sample.groupby("subject_id")["split"].nunique().max() == 1

    output_dir.mkdir(parents=True, exist_ok=True)
    sample.to_csv(output_dir / "sample_admissions_2000.csv", index=False)

    split_summary = (
        sample.groupby("split")
        .agg(
            admissions=("hadm_id", "size"),
            subjects=("subject_id", "nunique"),
            mortality_rate=("mortality_label", "mean"),
        )
        .reindex(["train", "val", "test"])
    )
    summary = {
        "random_seed": random_seed,
        "n_samples": int(len(sample)),
        "n_subjects": int(sample["subject_id"].nunique()),
        "window_hours": window_hours,
        "mortality_rate": float(sample["mortality_label"].mean()),
        "age_mean": float(sample["age"].mean()),
        "age_std": float(sample["age"].std()),
        "split_counts": split_summary.to_dict(orient="index"),
    }
    (output_dir / "sample_admissions_2000_summary.json").write_text(json.dumps(summary, indent=2))
    return sample


def extract_irregular_stream(
    csv_path: Path,
    itemids: list[int],
    variable_name: str,
    source_name: str,
    sample: pd.DataFrame,
    chunksize: int,
    window_hours: int,
) -> pd.DataFrame:
    usecols = ["SUBJECT_ID", "HADM_ID", "ITEMID", "CHARTTIME", "VALUENUM"]
    target_hadm = set(sample["hadm_id"].astype(int))
    windows = sample[["subject_id", "hadm_id", "window_start", "window_end"]].copy()
    windows["window_start"] = pd.to_datetime(windows["window_start"])
    windows["window_end"] = pd.to_datetime(windows["window_end"])
    windows["hadm_id"] = windows["hadm_id"].astype(int)

    pieces = []
    for chunk in pd.read_csv(csv_path, usecols=usecols, chunksize=chunksize):
        chunk = chunk.dropna(subset=["HADM_ID", "VALUENUM"]).copy()
        if chunk.empty:
            continue
        chunk["HADM_ID"] = chunk["HADM_ID"].astype(int)
        chunk = chunk.loc[chunk["HADM_ID"].isin(target_hadm) & chunk["ITEMID"].isin(itemids)].copy()
        if chunk.empty:
            continue
        chunk["CHARTTIME"] = pd.to_datetime(chunk["CHARTTIME"], errors="coerce")
        chunk = chunk.dropna(subset=["CHARTTIME"])
        chunk = chunk.rename(
            columns={
                "SUBJECT_ID": "subject_id",
                "HADM_ID": "hadm_id",
                "ITEMID": "itemid",
                "CHARTTIME": "chart_time",
                "VALUENUM": "value",
            }
        )
        chunk = chunk.merge(windows, on=["subject_id", "hadm_id"], how="inner")
        chunk = chunk.loc[
            chunk["chart_time"].ge(chunk["window_start"])
            & chunk["chart_time"].le(chunk["window_end"])
        ].copy()
        if chunk.empty:
            continue
        chunk["hours_since_admit"] = (
            chunk["chart_time"] - chunk["window_start"]
        ).dt.total_seconds() / 3600
        chunk["hours_since_admit"] = chunk["hours_since_admit"].clip(0, window_hours)
        chunk["variable"] = variable_name
        chunk["source"] = source_name
        chunk["mask"] = 1
        pieces.append(
            chunk[
                [
                    "subject_id",
                    "hadm_id",
                    "variable",
                    "source",
                    "itemid",
                    "chart_time",
                    "hours_since_admit",
                    "value",
                    "mask",
                ]
            ]
        )

    if not pieces:
        return pd.DataFrame(
            columns=[
                "subject_id",
                "hadm_id",
                "variable",
                "source",
                "itemid",
                "chart_time",
                "hours_since_admit",
                "value",
                "mask",
            ]
        )
    return pd.concat(pieces, ignore_index=True).sort_values(
        ["subject_id", "hadm_id", "hours_since_admit", "variable"]
    )


def build_temporal_events(
    mimic_dir: Path,
    output_dir: Path,
    sample: pd.DataFrame,
    chunksize: int,
    window_hours: int,
) -> None:
    heart_rate = extract_irregular_stream(
        mimic_dir / "CHARTEVENTS.csv",
        HEART_RATE_ITEMIDS,
        "heart_rate",
        "CHARTEVENTS",
        sample,
        chunksize,
        window_hours,
    )
    glucose = extract_irregular_stream(
        mimic_dir / "LABEVENTS.csv",
        GLUCOSE_LABITEMIDS,
        "glucose",
        "LABEVENTS",
        sample,
        chunksize,
        window_hours,
    )
    temporal_events = pd.concat([heart_rate, glucose], ignore_index=True).sort_values(
        ["subject_id", "hadm_id", "variable", "hours_since_admit"]
    )
    temporal_events.to_csv(output_dir / "temporal_events_2000.csv", index=False)

    coverage = (
        temporal_events.groupby(["hadm_id", "variable"]).size().unstack(fill_value=0).reset_index()
    )
    coverage.to_csv(output_dir / "temporal_coverage_2000.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mimic-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--n-samples", type=int, default=2000)
    parser.add_argument("--random-seed", type=int, default=2026)
    parser.add_argument("--window-hours", type=int, default=168)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    parser.add_argument("--run-full-extraction", action="store_true")
    args = parser.parse_args()

    required = ["ADMISSIONS.csv", "PATIENTS.csv", "CHARTEVENTS.csv", "LABEVENTS.csv", "D_LABITEMS.csv"]
    missing = [name for name in required if not (args.mimic_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required MIMIC-III files in {args.mimic_dir}: {missing}")

    sample = build_sample_admissions(
        mimic_dir=args.mimic_dir,
        output_dir=args.output_dir,
        n_samples=args.n_samples,
        random_seed=args.random_seed,
        window_hours=args.window_hours,
    )

    if args.run_full_extraction:
        build_temporal_events(
            mimic_dir=args.mimic_dir,
            output_dir=args.output_dir,
            sample=sample,
            chunksize=args.chunksize,
            window_hours=args.window_hours,
        )


if __name__ == "__main__":
    main()

