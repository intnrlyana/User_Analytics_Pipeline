import pandas as pd

from src.validation import validate_event_row


def build_row(**overrides):
    row = {
        "event_id": "evt_001",
        "session_token": "session_hash",
        "event_type": "page_view",
        "timestamp": "2026-07-01T12:00:00Z",
        "device_type": "Mobile",
        "response_time_ms": "120",
    }
    row.update(overrides)
    return pd.Series(row)


def test_valid_row_passes_validation():
    cleaned_row, error_reason = validate_event_row(build_row())

    assert error_reason is None
    assert cleaned_row["device_type"] == "mobile"
    assert cleaned_row["response_time_ms"] == 120


def test_invalid_device_type_is_rejected():
    cleaned_row, error_reason = validate_event_row(build_row(device_type="watch"))

    assert cleaned_row is None
    assert error_reason == "invalid device_type"


def test_negative_response_time_is_rejected():
    cleaned_row, error_reason = validate_event_row(build_row(response_time_ms="-1"))

    assert cleaned_row is None
    assert error_reason == "invalid response_time_ms"


def test_missing_session_token_is_rejected():
    cleaned_row, error_reason = validate_event_row(build_row(session_token=""))

    assert cleaned_row is None
    assert error_reason == "missing session_token"
