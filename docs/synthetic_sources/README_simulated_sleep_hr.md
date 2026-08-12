
# Simulated Sleep and Heart Rate Time Series Dataset (2024)

This dataset simulates irregular time series data for sleep and heart rate metrics, designed to represent user behavior over one calendar year (2024). The data is intended for experiments in machine learning, especially anomaly detection and irregular time series modeling.

## Files

- `simulated_sleep_data.csv`: Simulated nightly sleep data.
- `simulated_heart_rate_data.csv`: Simulated daytime physical activity heart rate data.

## Users

- 100 users (`user_id` 1 to 100).
- Each user has between 1 and 300 nights of sleep records.
- Each night is uniquely identified by a `sleep_id` = `user_id_YYYYMMDD`.

## Sleep Data

### Format
- Each row is a night of sleep for a user.
- Timestamps use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`.

### Variables
- `light`: seconds spent in light sleep.
- `rem`: seconds spent in REM sleep.
- `deep`: seconds spent in deep sleep.
- `fall_asleep`: time until user falls asleep.
- `awake`: time spent awake.
- All durations sum to a total between 14,400 and 36,000 seconds (4 to 10 hours).
- Proportions follow conventional adult sleep architecture (e.g., deep sleep: 13–23%).

### Anomalies
- 10% of records are marked as `is_anomalous = True` and contain missing sleep stage data.
- 10% of all records are duplicated with different values to simulate multiple devices reporting overlapping events.
- Devices: One of `Source_A` to `Source_F`.

## Heart Rate Data

### Format
- Each row corresponds to a physical activity event on the day **before** a recorded night of sleep.
- Events are between 6 and 24 hours before the sleep timestamp.
- Up to 10 events per day are simulated per user.

### Variables
- `activity`: Type of physical activity (`Walking` or `Cycling`).
- `duration_secs`: Event duration in seconds (5 minutes to 2 hours).
- `hr_min`, `hr_avg`, `hr_max`: Heart rate stats based on user profile.
  - Sedentary profile: HR min (60–70), avg (70–90), max (90–130).
  - Active profile: HR min (40–55), avg (55–75), max (75–190).
- 15% of records are marked as `is_anomalous = True` with implausible HR values (e.g., HR max > 200).
- 15% of the rows are duplicates to simulate data from different devices.

## User Demographics

A separate dataset is generated to assign demographic attributes to each `user_id`.
These attributes can be used for exploratory analysis, stratification, or modeling.

### Variables
- `user_id`: Same as in sleep and heart rate datasets.
- `age`: Random age between 18 and 69.
- `gender`: Randomly chosen from Male, Female, Other.
- `height_cm`: Normally distributed by gender.
- `weight_kg`: Normally distributed by gender.
- `bmi`: Body Mass Index calculated as weight (kg) / height (m)^2.
- `activity_level`: Random activity profile from ['Sedentary', 'Light', 'Moderate', 'Active', 'Athlete'].
- `primary_device`: Randomly chosen from ['Source_A', ..., 'Source_F'].

## Notes

- Timestamps are ordered from Jan to Dec 2024.
- The dataset is suitable for:
  - Time series forecasting
  - Classification
  - Missing data imputation
  - Anomaly detection
  - Device comparison