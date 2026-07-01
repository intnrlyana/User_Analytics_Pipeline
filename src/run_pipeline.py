import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import initialise_database
from src.run_ingestion import print_summary, run_ingestion_stage
from src.run_transform import print_transform_summary, run_transform_stage


def main() -> None:
    try:
        initialise_database()
        ingestion_stage = run_ingestion_stage(initialise_db=False)
        transform_stage = run_transform_stage(initialise_db=False)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")
        raise SystemExit(1) from error

    print("\nPipeline Run Complete")
    print("=====================")
    print_summary(
        ingestion_stage["ingestion_result"],
        ingestion_stage["loading_summary"],
    )
    print_transform_summary(transform_stage)


if __name__ == "__main__":
    main()
