import sys
from pathlib import Path
from typing import Any

import pandas as pd


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import PROJECT_ROOT, SAMPLE_CSV_PATH
from src.database import initialise_database
from src.ingestion import ingest_csv
from src.load_events import load_events


REJECTED_ROWS_PATH = PROJECT_ROOT / "logs" / "rejected_rows.csv"


def write_rejected_rows(rejected_rows: list[dict[str, object]]) -> None:
    REJECTED_ROWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rejected_rows).to_csv(REJECTED_ROWS_PATH, index=False)


def print_summary(
    ingestion_result: dict[str, object], loading_summary: dict[str, int]
) -> None:
    rejected_rows = ingestion_result["rejected_rows"]
    rejection_reasons = ingestion_result["rejection_reasons"]

    print("\nIngestion Summary")
    print("-----------------")
    print(f"Total rows read: {ingestion_result['total_rows']}")
    print(f"Valid rows: {len(ingestion_result['valid_rows'])}")
    print(f"Rejected rows: {len(rejected_rows)}")

    if rejection_reasons:
        print("\nRejection Reasons")
        print("-----------------")
        for reason, count in rejection_reasons.items():
            print(f"{reason}: {count}")

    print("\nLoading Summary")
    print("---------------")
    print(f"Attempted inserts: {loading_summary['attempted_inserts']}")
    print(f"Inserted rows: {loading_summary['inserted_rows']}")
    print(f"Skipped duplicates: {loading_summary['skipped_duplicates']}")
    print(f"\nRejected rows written to: {REJECTED_ROWS_PATH}")


def run_ingestion_stage(
    csv_path: Path = SAMPLE_CSV_PATH, initialise_db: bool = True
) -> dict[str, Any]:
    if initialise_db:
        initialise_database()

    ingestion_result = ingest_csv(csv_path)
    write_rejected_rows(ingestion_result["rejected_rows"])
    loading_summary = load_events(ingestion_result["valid_rows"], initialise_db=False)

    return {
        "ingestion_result": ingestion_result,
        "loading_summary": loading_summary,
    }


def main() -> None:
    try:
        stage_result = run_ingestion_stage()
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")
        raise SystemExit(1) from error

    print_summary(
        stage_result["ingestion_result"],
        stage_result["loading_summary"],
    )


if __name__ == "__main__":
    main()
