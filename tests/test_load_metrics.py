from src import database
from src.load_metrics import load_session_metrics


def test_session_metrics_upsert_is_safe_to_rerun(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_user_analytics.db"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)

    import src.load_metrics as load_metrics_module

    monkeypatch.setattr(load_metrics_module, "get_connection", database.get_connection)
    monkeypatch.setattr(
        load_metrics_module,
        "initialise_database",
        database.initialise_database,
    )

    first_metric = {
        "session_token": "session_a",
        "total_events": 1,
        "session_duration_seconds": 0.0,
        "dominant_device": "mobile",
        "average_latency_ms": 100.0,
        "first_event_time": "2026-07-01T12:00:00Z",
        "last_event_time": "2026-07-01T12:00:00Z",
    }
    updated_metric = {
        "session_token": "session_a",
        "total_events": 2,
        "session_duration_seconds": 60.0,
        "dominant_device": "desktop",
        "average_latency_ms": 150.0,
        "first_event_time": "2026-07-01T12:00:00Z",
        "last_event_time": "2026-07-01T12:01:00Z",
    }

    first_summary = load_session_metrics([first_metric])
    second_summary = load_session_metrics([updated_metric])

    with database.get_connection() as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM session_metrics").fetchone()[0]
        stored_metric = connection.execute(
            """
            SELECT total_events, dominant_device, average_latency_ms
            FROM session_metrics
            WHERE session_token = 'session_a'
            """
        ).fetchone()

    assert first_summary == {
        "attempted_upserts": 1,
        "upserted_sessions": 1,
    }
    assert second_summary == {
        "attempted_upserts": 1,
        "upserted_sessions": 1,
    }
    assert row_count == 1
    assert stored_metric == (2, "desktop", 150.0)
