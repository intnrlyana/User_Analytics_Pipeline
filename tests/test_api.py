from fastapi.testclient import TestClient
import pytest

from src import database
from src.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "api_test.db")
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)

    with TestClient(app) as test_client:
        seed_test_database()
        yield test_client


def seed_test_database() -> None:
    with database.get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO events (
                event_id,
                session_token,
                event_type,
                timestamp,
                device_type,
                response_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "evt_api_001",
                    "session_api_a",
                    "page_view",
                    "2026-07-01T12:00:00Z",
                    "desktop",
                    100,
                ),
                (
                    "evt_api_002",
                    "session_api_a",
                    "api_call",
                    "2026-07-01T12:01:00Z",
                    "desktop",
                    250,
                ),
            ],
        )
        connection.execute(
            """
            INSERT INTO session_metrics (
                session_token,
                total_events,
                session_duration_seconds,
                dominant_device,
                average_latency_ms,
                first_event_time,
                last_event_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "session_api_a",
                2,
                60.0,
                "desktop",
                175.0,
                "2026-07-01T12:00:00Z",
                "2026-07-01T12:01:00Z",
            ),
        )


def test_root_returns_200(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "USER_ANALYTICS_PIPELINE"


def test_get_sessions_returns_pagination_fields(client):
    response = client.get("/sessions")

    assert response.status_code == 200
    body = response.json()
    assert "page" in body
    assert "page_size" in body
    assert "total_sessions" in body
    assert "total_pages" in body
    assert "sessions" in body


def test_get_sessions_invalid_page_returns_validation_error(client):
    response = client.get("/sessions?page=0")

    assert response.status_code == 422


def test_get_session_unknown_token_returns_404(client):
    response = client.get("/sessions/unknown_session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found: unknown_session"


def test_get_metrics_summary_returns_top_level_fields(client):
    response = client.get("/metrics/summary")

    assert response.status_code == 200
    body = response.json()
    assert "total_events" in body
    assert "average_session_duration_seconds" in body
    assert "event_type_breakdown" in body
    assert "p95_latency_ms" in body
