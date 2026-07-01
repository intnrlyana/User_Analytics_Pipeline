from datetime import timezone
from numbers import Integral, Real
from typing import Any

import pandas as pd
from dateutil.parser import isoparse


EXPECTED_COLUMNS = [
    "event_id",
    "session_token",
    "event_type",
    "timestamp",
    "device_type",
    "response_time_ms",
]

ALLOWED_DEVICE_TYPES = {"mobile", "desktop", "tablet"}


def validate_csv_columns(data_frame: pd.DataFrame) -> None:
    missing_columns = [
        column for column in EXPECTED_COLUMNS if column not in data_frame.columns
    ]

    if missing_columns:
        missing_column_list = ", ".join(missing_columns)
        raise ValueError(f"Missing required CSV columns: {missing_column_list}")


def validate_event_row(row: pd.Series | dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    event_id = clean_text_value(row.get("event_id"))
    if not event_id:
        return None, "missing event_id"

    session_token = clean_text_value(row.get("session_token"))
    if not session_token:
        return None, "missing session_token"

    event_type = clean_text_value(row.get("event_type"))
    if not event_type:
        return None, "missing event_type"

    timestamp = clean_timestamp(row.get("timestamp"))
    if timestamp is None:
        return None, "invalid timestamp"

    device_type = clean_text_value(row.get("device_type")).lower()
    if device_type not in ALLOWED_DEVICE_TYPES:
        return None, "invalid device_type"

    response_time_ms = clean_response_time(row.get("response_time_ms"))
    if response_time_ms is None:
        return None, "invalid response_time_ms"

    cleaned_row = {
        "event_id": event_id,
        "session_token": session_token,
        "event_type": event_type,
        "timestamp": timestamp,
        "device_type": device_type,
        "response_time_ms": response_time_ms,
    }
    return cleaned_row, None


def clean_text_value(value: Any) -> str:
    if pd.isna(value):
        return ""

    return str(value).strip()


def clean_timestamp(value: Any) -> str | None:
    if pd.isna(value):
        return None

    try:
        parsed_timestamp = isoparse(str(value).strip())
    except (TypeError, ValueError):
        return None

    if parsed_timestamp.tzinfo is None:
        return None

    utc_timestamp = parsed_timestamp.astimezone(timezone.utc)
    return utc_timestamp.isoformat().replace("+00:00", "Z")


def clean_response_time(value: Any) -> int | None:
    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, Integral):
        response_time = int(value)
    elif isinstance(value, Real):
        if not float(value).is_integer():
            return None
        response_time = int(value)
    else:
        value_text = str(value).strip()
        if not value_text.isdigit():
            return None
        response_time = int(value_text)

    if response_time < 0:
        return None

    return response_time
