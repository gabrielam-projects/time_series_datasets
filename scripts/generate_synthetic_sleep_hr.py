#!/usr/bin/env python3
"""Generate synthetic sleep, heart-rate and user-demographic datasets."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


DEVICES = ["Source_A", "Source_B", "Source_C", "Source_D", "Source_E", "Source_F"]
ACTIVITIES = ["Cycling", "Walking", "Running", "Swimming", "Yoga", "Gym"]


def generate_sleep_stages(total_sleep_seconds: int) -> tuple[int, int, int, int, int]:
    deep = int(total_sleep_seconds * np.random.uniform(0.13, 0.23))
    rem = int(total_sleep_seconds * np.random.uniform(0.20, 0.25))
    light = int(total_sleep_seconds * np.random.uniform(0.45, 0.55))
    awake = int(total_sleep_seconds * np.random.uniform(0.03, 0.07))
    fall_asleep = total_sleep_seconds - (deep + rem + light + awake)
    return max(0, light), max(0, rem), max(0, deep), max(0, fall_asleep), max(0, awake)


def generate_sleep_records(
    num_users: int,
    min_days: int,
    max_days: int,
    year: int,
    anomaly_rate: float,
    duplicate_rate: float,
) -> pd.DataFrame:
    records = []
    for user_id in range(1, num_users + 1):
        num_nights = np.random.randint(min_days, max_days + 1)
        base_date = datetime(year, 1, 1)
        for day_idx in range(num_nights):
            date = base_date + timedelta(days=day_idx)
            sleep_start = datetime(
                date.year,
                date.month,
                date.day,
                np.random.randint(21, 24),
                np.random.randint(0, 60),
            )
            total_sleep = np.random.randint(14_400, 36_001)
            light, rem, deep, fall_asleep, awake = generate_sleep_stages(total_sleep)
            is_anomalous = random.random() < anomaly_rate
            if is_anomalous:
                light = rem = deep = fall_asleep = awake = np.nan
            records.append(
                {
                    "user_id": user_id,
                    "sleep_id": f"{user_id}_{date.strftime('%Y%m%d')}",
                    "timestamp": sleep_start.isoformat(),
                    "light": light,
                    "rem": rem,
                    "deep": deep,
                    "fall_asleep": fall_asleep,
                    "awake": awake,
                    "device": random.choice(DEVICES),
                    "is_anomalous": is_anomalous,
                }
            )

    duplicate_count = int(len(records) * duplicate_rate)
    for record in random.sample(records, duplicate_count):
        duplicate = record.copy()
        duplicate["device"] = random.choice(DEVICES)
        for stage in ["light", "rem", "deep", "fall_asleep", "awake"]:
            if pd.notnull(duplicate[stage]):
                duplicate[stage] += np.random.randint(-60, 60)
        records.append(duplicate)
    return pd.DataFrame(records)


def generate_heart_rate_records(
    sleep: pd.DataFrame,
    anomaly_rate: float,
    duplicate_rate: float,
) -> pd.DataFrame:
    records = []
    for _, sleep_row in sleep.iterrows():
        sleep_timestamp = datetime.fromisoformat(str(sleep_row["timestamp"]))
        for _ in range(np.random.randint(1, 11)):
            event_time = sleep_timestamp - timedelta(
                hours=np.random.randint(6, 24),
                minutes=np.random.randint(0, 60),
            )
            profile = np.random.choice(["sedentary", "active"])
            if profile == "sedentary":
                hr_min = np.random.randint(60, 71)
                hr_avg = np.random.randint(70, 91)
                hr_max = np.random.randint(90, 131)
            else:
                hr_min = np.random.randint(40, 56)
                hr_avg = np.random.randint(55, 76)
                hr_max = np.random.randint(75, 191)

            is_anomalous = random.random() < anomaly_rate
            if is_anomalous:
                hr_min = np.random.randint(20, 35)
                hr_avg = np.random.randint(35, 45)
                hr_max = np.random.randint(200, 220)

            records.append(
                {
                    "user_id": int(sleep_row["user_id"]),
                    "sleep_id": sleep_row["sleep_id"],
                    "timestamp": event_time.isoformat(),
                    "duration_secs": np.random.randint(300, 7200),
                    "activity": random.choice(ACTIVITIES),
                    "hr_min": hr_min,
                    "hr_avg": hr_avg,
                    "hr_max": hr_max,
                    "device": random.choice(DEVICES),
                    "is_anomalous": is_anomalous,
                }
            )

    duplicate_count = int(len(records) * duplicate_rate)
    for record in random.sample(records, duplicate_count):
        duplicate = record.copy()
        duplicate["device"] = random.choice(DEVICES)
        duplicate["hr_avg"] += np.random.randint(-3, 4)
        records.append(duplicate)
    return pd.DataFrame(records)


def generate_user_demographics(num_users: int, registered_at: str) -> pd.DataFrame:
    rows = []
    for user_id in range(1, num_users + 1):
        gender = random.choice(["Male", "Female", "Other"])
        if gender == "Male":
            height = np.random.normal(175, 7)
            weight = np.random.normal(78, 10)
        elif gender == "Female":
            height = np.random.normal(162, 6)
            weight = np.random.normal(65, 8)
        else:
            height = np.random.normal(168, 8)
            weight = np.random.normal(72, 9)

        height = round(float(height), 1)
        weight = round(float(weight), 1)
        bmi = round(weight / ((height / 100) ** 2), 1)
        rows.append(
            {
                "user_id": user_id,
                "registered_at": registered_at,
                "age": np.random.randint(18, 70),
                "gender": gender,
                "height_cm": height,
                "weight_kg": weight,
                "bmi": bmi,
                "activity_level": random.choices(
                    ["Sedentary", "Light", "Moderate", "Active", "Athlete"],
                    weights=[0.2, 0.3, 0.3, 0.15, 0.05],
                )[0],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/public/synthetic"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-users", type=int, default=100)
    parser.add_argument("--min-days", type=int, default=1)
    parser.add_argument("--max-days", type=int, default=300)
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--sleep-anomaly-rate", type=float, default=0.15)
    parser.add_argument("--hr-anomaly-rate", type=float, default=0.15)
    parser.add_argument("--duplicate-rate", type=float, default=0.10)
    parser.add_argument("--registered-at", default="2025-07-03T11:51:06")
    args = parser.parse_args()

    np.random.seed(args.seed)
    random.seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sleep = generate_sleep_records(
        num_users=args.num_users,
        min_days=args.min_days,
        max_days=args.max_days,
        year=args.year,
        anomaly_rate=args.sleep_anomaly_rate,
        duplicate_rate=args.duplicate_rate,
    )
    heart_rate = generate_heart_rate_records(
        sleep=sleep,
        anomaly_rate=args.hr_anomaly_rate,
        duplicate_rate=args.duplicate_rate,
    )
    users = generate_user_demographics(args.num_users, args.registered_at)

    sleep.to_csv(args.output_dir / "simulated_sleep_data.csv", index=False)
    heart_rate.to_csv(args.output_dir / "simulated_heart_rate_data.csv", index=False)
    users.to_csv(args.output_dir / "simulated_user_data.csv", index=False)

    print(f"Wrote {len(sleep):,} sleep rows")
    print(f"Wrote {len(heart_rate):,} heart-rate rows")
    print(f"Wrote {len(users):,} user rows")


if __name__ == "__main__":
    main()

