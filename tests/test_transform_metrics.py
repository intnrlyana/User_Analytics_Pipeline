from src.transform_metrics import (
    build_session_metrics,
    calculate_average_latency_ms,
    calculate_session_duration_seconds,
    get_dominant_device,
)


def test_session_duration_calculation():
    duration = calculate_session_duration_seconds(
        "2026-07-01T12:00:00Z",
        "2026-07-01T12:02:30Z",
    )

    assert duration == 150.0


def test_dominant_device_calculation():
    dominant_device = get_dominant_device(["mobile", "desktop", "mobile"])

    assert dominant_device == "mobile"


def test_dominant_device_tie_breaks_alphabetically():
    dominant_device = get_dominant_device(["tablet", "mobile", "desktop"])

    assert dominant_device == "desktop"


def test_average_latency_calculation():
    average_latency = calculate_average_latency_ms([100, 101, 9500])

    assert average_latency == 3233.67


def test_build_session_metrics_uses_event_rows():
    events = [
        {
            "event_id": "evt_001",
            "session_token": "session_a",
            "event_type": "page_view",
            "timestamp": "2026-07-01T12:00:00Z",
            "device_type": "mobile",
            "response_time_ms": 100,
        },
        {
            "event_id": "evt_002",
            "session_token": "session_a",
            "event_type": "api_call",
            "timestamp": "2026-07-01T12:01:00Z",
            "device_type": "desktop",
            "response_time_ms": 200,
        },
    ]

    metrics = build_session_metrics(events)

    assert metrics == [
        {
            "session_token": "session_a",
            "total_events": 2,
            "session_duration_seconds": 60.0,
            "dominant_device": "desktop",
            "average_latency_ms": 150.0,
            "first_event_time": "2026-07-01T12:00:00Z",
            "last_event_time": "2026-07-01T12:01:00Z",
        }
    ]
