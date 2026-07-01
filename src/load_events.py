from typing import Any

from src.database import get_connection, initialise_database


INSERT_EVENT_SQL = """
INSERT OR IGNORE INTO events (
    event_id,
    session_token,
    event_type,
    timestamp,
    device_type,
    response_time_ms
) VALUES (
    :event_id,
    :session_token,
    :event_type,
    :timestamp,
    :device_type,
    :response_time_ms
);
"""


def load_events(
    valid_rows: list[dict[str, Any]], initialise_db: bool = True
) -> dict[str, int]:
    if initialise_db:
        initialise_database()

    inserted_rows = 0

    with get_connection() as connection:
        for row in valid_rows:
            # event_id is the primary key, so duplicates are skipped safely.
            cursor = connection.execute(INSERT_EVENT_SQL, row)
            inserted_rows += cursor.rowcount

    attempted_inserts = len(valid_rows)
    return {
        "attempted_inserts": attempted_inserts,
        "inserted_rows": inserted_rows,
        "skipped_duplicates": attempted_inserts - inserted_rows,
    }
