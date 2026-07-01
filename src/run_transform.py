import sys
from pathlib import Path
from typing import Any


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import initialise_database
from src.load_metrics import load_session_metrics
from src.transform_metrics import transform_session_metrics


def run_transform_stage(initialise_db: bool = True) -> dict[str, Any]:
    if initialise_db:
        initialise_database()

    session_metrics = transform_session_metrics()
    if not session_metrics:
        return {
            "session_metrics": [],
            "loading_summary": {
                "attempted_upserts": 0,
                "upserted_sessions": 0,
            },
        }

    loading_summary = load_session_metrics(session_metrics, initialise_db=False)

    return {
        "session_metrics": session_metrics,
        "loading_summary": loading_summary,
    }


def print_transform_summary(stage_result: dict[str, Any]) -> None:
    session_metrics = stage_result["session_metrics"]
    loading_summary = stage_result["loading_summary"]

    print("\nTransformation Summary")
    print("----------------------")

    if not session_metrics:
        print("No events found in the database. Run ingestion first:")
        print("python src/run_ingestion.py")
        return

    print(f"Sessions transformed: {len(session_metrics)}")

    print("\nMetrics Loading Summary")
    print("-----------------------")
    print(f"Attempted upserts: {loading_summary['attempted_upserts']}")
    print(f"Upserted sessions: {loading_summary['upserted_sessions']}")


def main() -> None:
    stage_result = run_transform_stage()
    print_transform_summary(stage_result)


if __name__ == "__main__":
    main()
