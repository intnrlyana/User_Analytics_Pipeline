from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from src.validation import EXPECTED_COLUMNS, validate_csv_columns, validate_event_row


def ingest_csv(csv_path: Path) -> dict[str, Any]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    data_frame = pd.read_csv(csv_path)
    validate_csv_columns(data_frame)

    valid_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    rejection_reasons: Counter[str] = Counter()

    for row_number, row in data_frame.iterrows():
        cleaned_row, error_reason = validate_event_row(row)

        if cleaned_row is not None:
            valid_rows.append(cleaned_row)
            continue

        rejection_reason = error_reason or "unknown validation error"
        rejection_reasons[rejection_reason] += 1
        rejected_rows.append(build_rejected_row(row_number, row, rejection_reason))

    return {
        "total_rows": len(data_frame),
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "rejection_reasons": dict(rejection_reasons),
    }


def build_rejected_row(
    row_number: int, row: pd.Series, rejection_reason: str
) -> dict[str, Any]:
    rejected_row = {
        column: row.get(column)
        for column in EXPECTED_COLUMNS
    }
    rejected_row["source_row_number"] = row_number + 2
    rejected_row["rejection_reason"] = rejection_reason
    return rejected_row
