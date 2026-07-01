import sys
from pathlib import Path

import pandas as pd
from dateutil.parser import isoparse


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import SAMPLE_CSV_PATH


EXPECTED_COLUMNS = [
    "event_id",
    "session_token",
    "event_type",
    "timestamp",
    "device_type",
    "response_time_ms",
]


def is_valid_timestamp(value: object) -> bool:
    if pd.isna(value):
        return False

    try:
        isoparse(str(value))
    except (TypeError, ValueError):
        return False

    return True


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def profile_csv() -> None:
    if not SAMPLE_CSV_PATH.exists():
        print(f"CSV file not found: {SAMPLE_CSV_PATH}")
        print("Run: python src/generate_sample_data.py")
        return

    data_frame = pd.read_csv(SAMPLE_CSV_PATH)

    print_section("Data Quality Profile")
    print(f"File: {SAMPLE_CSV_PATH}")
    print(f"Total rows: {len(data_frame)}")

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in data_frame.columns]
    if missing_columns:
        print(f"Missing expected columns: {', '.join(missing_columns)}")
        return

    response_times = pd.to_numeric(data_frame["response_time_ms"], errors="coerce")
    invalid_response_times = response_times.isna() | (response_times < 0)
    invalid_timestamps = ~data_frame["timestamp"].apply(is_valid_timestamp)

    print_section("Missing Values")
    print(data_frame[EXPECTED_COLUMNS].isna().sum().to_string())

    print_section("Uniqueness and Validity")
    print(f"Duplicate event_id count: {data_frame['event_id'].duplicated().sum()}")
    print(f"Invalid timestamp count: {invalid_timestamps.sum()}")
    print(f"Invalid or negative response_time_ms count: {invalid_response_times.sum()}")

    print_section("Response Time Summary")
    print(response_times.describe().to_string())

    clean_response_times = response_times.dropna()
    first_quartile = clean_response_times.quantile(0.25)
    third_quartile = clean_response_times.quantile(0.75)
    iqr = third_quartile - first_quartile
    lower_bound = first_quartile - (1.5 * iqr)
    upper_bound = third_quartile + (1.5 * iqr)
    outlier_count = ((clean_response_times < lower_bound) | (clean_response_times > upper_bound)).sum()

    print_section("Latency Outliers")
    print(f"IQR lower bound: {lower_bound:.2f}")
    print(f"IQR upper bound: {upper_bound:.2f}")
    print(f"Outlier count: {outlier_count}")

    print_section("Event Type Breakdown")
    print(data_frame["event_type"].value_counts(dropna=False).to_string())

    print_section("Device Type Breakdown")
    print(data_frame["device_type"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    profile_csv()
