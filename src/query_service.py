import math
import sqlite3
from typing import Any

from src import database


SESSION_METRIC_COLUMNS = """
    session_token,
    total_events,
    session_duration_seconds,
    dominant_device,
    average_latency_ms,
    first_event_time,
    last_event_time
"""


def get_sessions(page: int, page_size: int) -> dict[str, Any]:
    offset = (page - 1) * page_size

    with get_read_connection() as connection:
        total_sessions = connection.execute(
            "SELECT COUNT(*) AS count FROM session_metrics"
        ).fetchone()["count"]
        rows = connection.execute(
            f"""
            SELECT {SESSION_METRIC_COLUMNS}
            FROM session_metrics
            ORDER BY session_token
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()

    return {
        "sessions": rows_to_dicts(rows),
        "total_sessions": total_sessions,
    }


def get_session_by_token(session_token: str) -> dict[str, Any] | None:
    with get_read_connection() as connection:
        row = connection.execute(
            f"""
            SELECT {SESSION_METRIC_COLUMNS}
            FROM session_metrics
            WHERE session_token = ?
            """,
            (session_token,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_metrics_summary() -> dict[str, Any]:
    with get_read_connection() as connection:
        total_events = connection.execute(
            "SELECT COUNT(*) AS count FROM events"
        ).fetchone()["count"]
        average_duration = connection.execute(
            """
            SELECT AVG(session_duration_seconds) AS average_duration
            FROM session_metrics
            """
        ).fetchone()["average_duration"]
        event_type_rows = connection.execute(
            """
            SELECT event_type, COUNT(*) AS count
            FROM events
            GROUP BY event_type
            ORDER BY event_type
            """
        ).fetchall()
        latency_rows = connection.execute(
            """
            SELECT response_time_ms
            FROM events
            ORDER BY response_time_ms
            """
        ).fetchall()

    return {
        "total_events": total_events,
        "average_session_duration_seconds": round(average_duration or 0.0, 2),
        "event_type_breakdown": {
            row["event_type"]: row["count"] for row in event_type_rows
        },
        "p95_latency_ms": calculate_p95_latency(
            [row["response_time_ms"] for row in latency_rows]
        ),
    }


def calculate_total_pages(total_items: int, page_size: int) -> int:
    if total_items == 0:
        return 0

    return math.ceil(total_items / page_size)


def calculate_p95_latency(latencies: list[int]) -> float | None:
    if not latencies:
        return None

    # SQLite has no built in percentile aggregate, so p95 is calculated directly in Python
    sorted_latencies = sorted(latencies)
    percentile_position = 0.95 * (len(sorted_latencies) - 1)
    lower_index = math.floor(percentile_position)
    upper_index = math.ceil(percentile_position)

    if lower_index == upper_index:
        return float(sorted_latencies[lower_index])

    lower_value = sorted_latencies[lower_index]
    upper_value = sorted_latencies[upper_index]
    weight = percentile_position - lower_index
    return round(lower_value + ((upper_value - lower_value) * weight), 2)


def get_read_connection() -> sqlite3.Connection:
    connection = database.get_connection()
    # Row objects allow query results to be converted into response dictionaries
    connection.row_factory = sqlite3.Row
    return connection


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
