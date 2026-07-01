import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import DATA_DIR, SAMPLE_CSV_PATH


FIELDNAMES = [
    "event_id",
    "session_token",
    "event_type",
    "timestamp",
    "device_type",
    "response_time_ms",
]

EVENT_TYPES = ["page_view", "button_click", "api_call"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]


def build_valid_rows() -> list[dict[str, object]]:
    random.seed(42)
    rows: list[dict[str, object]] = []
    base_time = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)

    for session_number in range(1, 13):
        session_token = f"session_{session_number:03d}_hash"
        device_type = random.choice(DEVICE_TYPES)
        events_in_session = random.randint(7, 10)
        session_start = base_time + timedelta(minutes=session_number * 8)

        for event_index in range(events_in_session):
            event_time = session_start + timedelta(seconds=event_index * random.randint(20, 90))
            response_time_ms = max(20, int(random.gauss(180, 55)))

            rows.append(
                {
                    "event_id": f"evt_{len(rows) + 1:04d}",
                    "session_token": session_token,
                    "event_type": random.choice(EVENT_TYPES),
                    "timestamp": event_time.isoformat().replace("+00:00", "Z"),
                    "device_type": device_type,
                    "response_time_ms": response_time_ms,
                }
            )

    return rows


def build_malformed_rows() -> list[dict[str, object]]:
    return [
        {
            "event_id": "evt_0001",
            "session_token": "session_duplicate_hash",
            "event_type": "page_view",
            "timestamp": "2026-07-01T12:00:00Z",
            "device_type": "desktop",
            "response_time_ms": 140,
        },
        {
            "event_id": "evt_bad_missing_session",
            "session_token": "",
            "event_type": "api_call",
            "timestamp": "2026-07-01T12:01:00Z",
            "device_type": "mobile",
            "response_time_ms": 220,
        },
        {
            "event_id": "evt_bad_timestamp",
            "session_token": "session_bad_timestamp_hash",
            "event_type": "button_click",
            "timestamp": "not-a-timestamp",
            "device_type": "tablet",
            "response_time_ms": 95,
        },
        {
            "event_id": "evt_bad_device",
            "session_token": "session_bad_device_hash",
            "event_type": "page_view",
            "timestamp": "2026-07-01T12:03:00Z",
            "device_type": "watch",
            "response_time_ms": 130,
        },
        {
            "event_id": "evt_bad_negative_latency",
            "session_token": "session_bad_latency_hash",
            "event_type": "api_call",
            "timestamp": "2026-07-01T12:04:00Z",
            "device_type": "desktop",
            "response_time_ms": -30,
        },
        {
            "event_id": "evt_latency_outlier",
            "session_token": "session_outlier_hash",
            "event_type": "api_call",
            "timestamp": "2026-07-01T12:05:00Z",
            "device_type": "mobile",
            "response_time_ms": 9500,
        },
    ]


def write_sample_csv(rows: list[dict[str, object]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with SAMPLE_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_valid_rows()
    rows.extend(build_malformed_rows())
    write_sample_csv(rows)
    print(f"Wrote {len(rows)} rows to {SAMPLE_CSV_PATH}")


if __name__ == "__main__":
    main()
