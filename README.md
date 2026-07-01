# User Analytics Pipeline

## Project Overview

USER_ANALYTICS_PIPELINE is a lightweight backend data pipeline for application event logs. The project is designed as a take-home assessment: clear structure, small focused modules, and enough implementation to show practical data engineering judgment without over-building.

The intended flow is:

```text
CSV event logs -> validation and cleaning -> SQLite storage -> session metrics -> FastAPI API
```

Stage 1 created the project foundation, database schema, sample data generator, and data profiling script. Stage 2 added CSV ingestion, row validation, rejected-row logging, and idempotent loading into SQLite. Stage 3 adds session-level transformation and loading into `session_metrics`.

## Assessment Mapping

This project addresses the assessment objective by setting up the first pieces of an end-to-end analytics pipeline:

- Ingest raw application events from CSV.
- Profile data quality before loading.
- Store raw events and session-level metrics in a relational database.
- Prepare the codebase for validation, transformation, and API access.

The current project intentionally stops before building the API so each part can remain reviewable.

## Architecture Overview

The project is organized around one responsibility per file:

- `data/sample_events.csv`: small synthetic event log dataset.
- `src/config.py`: central project paths.
- `src/database.py`: SQLite connection and schema initialization.
- `src/generate_sample_data.py`: creates realistic sample CSV data with known bad rows.
- `src/validation.py`: validates and cleans individual event rows.
- `src/ingestion.py`: reads CSV data and separates valid rows from rejected rows.
- `src/load_events.py`: loads valid events into SQLite safely.
- `src/run_ingestion.py`: command-line entry point for Stage 2 ingestion.
- `src/transform_metrics.py`: computes session-level metrics from stored events.
- `src/load_metrics.py`: upserts transformed metrics into SQLite.
- `src/run_transform.py`: command-line entry point for Stage 3 transformation.
- `src/run_pipeline.py`: runs ingestion, event loading, transformation, and metric loading.
- `src/profile_data.py`: prints data quality checks for the CSV.
- `sql/schema.sql`: relational database schema.
- `tests/`: lightweight pytest coverage for validation, loading, and transformation logic.

Future stages will add REST API modules.

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

## Stage 2: Ingestion and Validation

Stage 2 reads `data/sample_events.csv`, validates the expected schema, cleans valid rows, writes malformed rows to `logs/rejected_rows.csv`, and loads valid events into the `events` table.

Validation rules:

- Required columns must exist: `event_id`, `session_token`, `event_type`, `timestamp`, `device_type`, and `response_time_ms`.
- `event_id`, `session_token`, and `event_type` must not be empty.
- `timestamp` must be parseable as an ISO 8601 timestamp with timezone information.
- `device_type` must be `mobile`, `desktop`, or `tablet`. Input is accepted case-insensitively and stored in lowercase.
- `response_time_ms` must be an integer greater than or equal to zero.
- Very high `response_time_ms` values are kept during ingestion. They are treated as profiling outliers, not invalid records.

Malformed rows are skipped instead of crashing the pipeline. Each rejected row is written with its source row number and rejection reason so the issue can be reviewed later.

Loading is idempotent because `event_id` is the primary key and inserts use SQLite `INSERT OR IGNORE`. Re-running the same CSV will not duplicate events; duplicate `event_id` values are counted as skipped duplicates.

Run Stage 2 ingestion:

```bash
python src/run_ingestion.py
```

Expected terminal output includes:

- total rows read
- valid row count
- rejected row count
- rejection reason summary
- attempted inserts
- inserted rows
- skipped duplicates
- rejected-row log location

## Stage 3: Session Metrics Transformation

Stage 3 reads valid events from the SQLite `events` table and computes one metrics row per `session_token`. It does not recompute metrics directly from the CSV. This keeps ingestion and transformation separate and makes the database the source of truth after validation.

Aggregation logic:

- `total_events`: count all stored events for the session.
- `first_event_time`: earliest event timestamp for the session.
- `last_event_time`: latest event timestamp for the session.
- `session_duration_seconds`: difference between `last_event_time` and `first_event_time` in seconds. A one-event session has duration `0`.
- `dominant_device`: most frequent `device_type` in the session. Ties are resolved alphabetically, so `desktop` comes before `mobile`, and `mobile` comes before `tablet`.
- `average_latency_ms`: average `response_time_ms`, rounded to two decimal places. Valid high-latency outliers are included in the average.

Metrics loading is idempotent. The `session_metrics` table uses `session_token` as the primary key, and loading uses SQLite upsert logic:

```sql
INSERT ... ON CONFLICT(session_token) DO UPDATE
```

Re-running the transformation updates the existing metrics row for each session instead of creating duplicates.

Run ingestion only when the CSV has changed or the `events` table needs to be populated:

```bash
python src/run_ingestion.py
```

Run transformation only when valid events are already loaded and session metrics need to be refreshed:

```bash
python src/run_transform.py
```

Run the full local pipeline when you want ingestion, validation, event loading, transformation, and metrics loading in one command:

```bash
python src/run_pipeline.py
```

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

- Expose query endpoints through a FastAPI REST API.
- Add API-level tests for query behavior.

## Production Considerations

For production, this design would need stronger operational support:

- Use PostgreSQL instead of SQLite for concurrent reads and writes.
- Add structured logging and pipeline run metadata.
- Track rejected records with clear error reasons.
- Add database migrations instead of manually running one schema file.
- Add automated tests in CI.
- Add API authentication and rate limiting.
- Add monitoring for data freshness, volume changes, and latency outliers.

Production orchestration would look like:

```text
CSV available
-> scheduled trigger
-> ingestion
-> validation
-> rejected row logging
-> load events
-> transform session metrics
-> upsert session_metrics
-> API serves updated results
-> logs, retries, and alerts in production
```

In local development, run the full flow manually:

```bash
python src/run_pipeline.py
```

In production, the same flow could be scheduled using cron, Airflow, GitHub Actions, or a containerised job. Failed runs should be logged and alerted. Idempotency is achieved through `event_id` uniqueness in `events` and `session_token` upserts in `session_metrics`.
