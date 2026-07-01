import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from dateutil.parser import isoparse

from src.database import get_connection


EVENT_QUERY = """
SELECT
    event_id,
    session_token,
    event_type,
    timestamp,
    device_type,
    response_time_ms
FROM events
ORDER BY session_token, timestamp, event_id;
"""


def fetch_events() -> list[dict[str, Any]]:
    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(EVENT_QUERY).fetchall()

    return [dict(row) for row in rows]


def transform_session_metrics() -> list[dict[str, Any]]:
    events = fetch_events()
    return build_session_metrics(events)


def build_session_metrics(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for event in events:
        sessions[event["session_token"]].append(event)

    metrics: list[dict[str, Any]] = []

    for session_token in sorted(sessions):
        session_events = sorted(
            sessions[session_token],
            key=lambda event: parse_timestamp(event["timestamp"]),
        )
        first_event_time = session_events[0]["timestamp"]
        last_event_time = session_events[-1]["timestamp"]

        metrics.append(
            {
                "session_token": session_token,
                "total_events": len(session_events),
                "session_duration_seconds": calculate_session_duration_seconds(
                    first_event_time,
                    last_event_time,
                ),
                "dominant_device": get_dominant_device(
                    [event["device_type"] for event in session_events]
                ),
                "average_latency_ms": calculate_average_latency_ms(
                    [event["response_time_ms"] for event in session_events]
                ),
                "first_event_time": first_event_time,
                "last_event_time": last_event_time,
            }
        )

    return metrics


def calculate_session_duration_seconds(
    first_event_time: str, last_event_time: str
) -> float:
    first_timestamp = parse_timestamp(first_event_time)
    last_timestamp = parse_timestamp(last_event_time)
    return max((last_timestamp - first_timestamp).total_seconds(), 0.0)


def get_dominant_device(device_types: list[str]) -> str:
    device_counts = Counter(device_types)
    # Sort by highest count first, then alphabetically for deterministic ties.
    return sorted(device_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def calculate_average_latency_ms(response_times: list[int]) -> float:
    return round(sum(response_times) / len(response_times), 2)


def parse_timestamp(timestamp: str) -> datetime:
    return isoparse(timestamp)
