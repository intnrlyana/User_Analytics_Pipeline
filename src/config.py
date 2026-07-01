from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "user_analytics.db"
SAMPLE_CSV_PATH = DATA_DIR / "sample_events.csv"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
