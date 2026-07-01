# User Analytics Pipeline

## Project Overview

USER_ANALYTICS_PIPELINE is a lightweight backend data pipeline for application event logs. The project is designed as a take-home assessment: clear structure, small focused modules, and enough implementation to show practical data engineering judgment without over-building.

The intended flow is:

```text
CSV event logs -> validation and cleaning -> SQLite storage -> session metrics -> FastAPI API
```

Stage 1 creates the project foundation, database schema, sample data generator, and data profiling script. The API and full transformation pipeline are planned for later stages.

## Assessment Mapping

This project addresses the assessment objective by setting up the first pieces of an end-to-end analytics pipeline:

- Ingest raw application events from CSV.
- Profile data quality before loading.
- Store raw events and session-level metrics in a relational database.
- Prepare the codebase for validation, transformation, and API access.

The current stage intentionally stops before building the API so each part can remain reviewable.

## Architecture Overview

The project is organized around one responsibility per file:

- `data/sample_events.csv`: small synthetic event log dataset.
- `src/config.py`: central project paths.
- `src/database.py`: SQLite connection and schema initialization.
- `src/generate_sample_data.py`: creates realistic sample CSV data with known bad rows.
- `src/profile_data.py`: prints data quality checks for the CSV.
- `sql/schema.sql`: relational database schema.
- `tests/`: reserved for automated tests in later stages.

Future stages will add validation, cleaning, session metric transformation, loading, and REST API modules.

## Database Choice

SQLite is used for this assessment because it is free, serverless, lightweight, and easy for reviewers to run locally. It works well for a CSV-based batch pipeline and keeps setup friction low.

For a larger production deployment, PostgreSQL would be a better upgrade. PostgreSQL provides stronger concurrency support, richer indexing options, better operational tooling, stricter production-grade access control, and better support for larger workloads.

## Database Schema

The database contains two main tables.

`events` stores cleaned raw event records. It keeps one row per event and uses `event_id` as the primary key to prevent duplicate event ingestion.

`session_metrics` stores aggregated behavioral metrics for each session. It is designed to support API queries without recalculating session statistics on every request.

Indexes are included for common query patterns:

- `events(session_token)`: speeds up lookup of all events for a session.
- `events(timestamp)`: supports time-based filtering and ordering.
- `events(event_type)`: supports event-type breakdowns and filters.
- `session_metrics(average_latency_ms)`: supports latency-based ranking and filtering.

## Data Profiling

The profiling script reads `data/sample_events.csv` and reports:

- total row count
- missing values by column
- duplicate `event_id` count
- invalid or negative `response_time_ms` count
- response time summary statistics
- simple IQR-based latency outlier detection
- `event_type` breakdown
- `device_type` breakdown

This gives a reviewer a quick view of data quality before any cleaning or loading happens.

## How to Run Stage 1

Create and activate a virtual environment if needed, then install dependencies:

```bash
pip install -r requirements.txt
```

Generate the sample CSV:

```bash
python src/generate_sample_data.py
```

Profile the sample data:

```bash
python src/profile_data.py
```

Initialize the SQLite database:

```bash
python -c "from src.database import initialise_database; initialise_database()"
```

The database file is created at `data/user_analytics.db`.

## Planned Next Steps

- Add validation rules for required fields, timestamps, device types, and latency values.
- Clean invalid records into accepted and rejected datasets.
- Load validated events into SQLite.
- Transform event rows into session-level metrics.
- Add tests for validation and transformation logic.
- Expose query endpoints through a FastAPI REST API.

## Production Considerations

For production, this design would need stronger operational support:

- Use PostgreSQL instead of SQLite for concurrent reads and writes.
- Add structured logging and pipeline run metadata.
- Track rejected records with clear error reasons.
- Add database migrations instead of manually running one schema file.
- Add automated tests in CI.
- Add API authentication and rate limiting.
- Add monitoring for data freshness, volume changes, and latency outliers.
