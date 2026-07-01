from src import database
from src.load_events import load_events


def test_duplicate_event_id_does_not_break_loading(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_user_analytics.db"
    schema_path = database.SCHEMA_PATH

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)

    import src.load_events as load_events_module

    monkeypatch.setattr(load_events_module, "get_connection", database.get_connection)
    monkeypatch.setattr(load_events_module, "initialise_database", database.initialise_database)

    valid_rows = [
        {
            "event_id": "evt_duplicate",
            "session_token": "session_hash",
            "event_type": "page_view",
            "timestamp": "2026-07-01T12:00:00Z",
            "device_type": "desktop",
            "response_time_ms": 100,
        },
        {
            "event_id": "evt_duplicate",
            "session_token": "session_hash",
            "event_type": "api_call",
            "timestamp": "2026-07-01T12:01:00Z",
            "device_type": "desktop",
            "response_time_ms": 150,
        },
    ]

    assert schema_path.exists()

    first_summary = load_events(valid_rows)
    second_summary = load_events(valid_rows)

    assert first_summary == {
        "attempted_inserts": 2,
        "inserted_rows": 1,
        "skipped_duplicates": 1,
    }
    assert second_summary == {
        "attempted_inserts": 2,
        "inserted_rows": 0,
        "skipped_duplicates": 2,
    }
