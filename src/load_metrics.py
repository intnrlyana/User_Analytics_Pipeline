from typing import Any

from src.database import get_connection, initialise_database


UPSERT_SESSION_METRIC_SQL = """
INSERT INTO session_metrics (
    session_token,
    total_events,
    session_duration_seconds,
    dominant_device,
    average_latency_ms,
    first_event_time,
    last_event_time
) VALUES (
    :session_token,
    :total_events,
    :session_duration_seconds,
    :dominant_device,
    :average_latency_ms,
    :first_event_time,
    :last_event_time
)
ON CONFLICT(session_token) DO UPDATE SET
    total_events = excluded.total_events,
    session_duration_seconds = excluded.session_duration_seconds,
    dominant_device = excluded.dominant_device,
    average_latency_ms = excluded.average_latency_ms,
    first_event_time = excluded.first_event_time,
    last_event_time = excluded.last_event_time,
    updated_at = CURRENT_TIMESTAMP;
"""


def load_session_metrics(
    session_metrics: list[dict[str, Any]], initialise_db: bool = True
) -> dict[str, int]:
    if initialise_db:
        initialise_database()

    with get_connection() as connection:
        for metric in session_metrics:
            connection.execute(UPSERT_SESSION_METRIC_SQL, metric)

    attempted_upserts = len(session_metrics)
    return {
        "attempted_upserts": attempted_upserts,
        "upserted_sessions": attempted_upserts,
    }
