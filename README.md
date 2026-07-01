# User Analytics Pipeline

USER_ANALYTICS_PIPELINE is a lightweight backend data pipeline for application event logs. It ingests raw CSV events, validates and cleans rows, stores valid events in SQLite, transforms them into session-level metrics, and exposes the results through a FastAPI REST API.

The project is intentionally small, modular, and easy to run in a local development environment. The code is split by responsibility so each part of the pipeline can be inspected independently.

## Architecture Overview

```text
+-------------------+      +--------------------------+      +----------------+
| Raw CSV Events    | ---> | Ingestion + Validation   | ---> | SQLite events  |
| sample_events.csv |      | log rejected rows        |      | table          |
+-------------------+      +--------------------------+      +----------------+
                                                                    |
                                                                    v
                                                           +---------------------+
                                                           | Session Metrics     |
                                                           | transformation      |
                                                           +---------------------+
                                                                    |
                                                                    v
                                                           +---------------------+
                                                           | SQLite              |
                                                           | session_metrics     |
                                                           +---------------------+
                                                                    |
                                                                    v
                                                           +---------------------+
                                                           | FastAPI API         |
                                                           | /sessions, summary  |
                                                           +---------------------+
```

## Quick Start

Run these commands from the project root.

Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/generate_sample_data.py
python src/profile_data.py
python src/run_pipeline.py
pytest
uvicorn src.main:app --reload
```

macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/generate_sample_data.py
python src/profile_data.py
python src/run_pipeline.py
pytest
uvicorn src.main:app --reload
```

Open Swagger UI at:

```text
http://localhost:8000/docs
```

The `uvicorn` command keeps the API server running in that terminal. Generated files such as `data/user_analytics.db` and `logs/rejected_rows.csv` are ignored by git.

## Implementation Coverage

| Requirement area | How this project satisfies it |
| --- | --- |
| Data exploration | `src/profile_data.py` reports nulls, duplicate `event_id` values, latency summary statistics, IQR outliers, event type counts, and device type counts. |
| Data modelling | `sql/schema.sql` defines `events` for cleaned raw events and `session_metrics` for API-ready session aggregates. |
| Ingestion | `src/ingestion.py` reads the CSV with pandas, validates required columns, validates each row, and separates accepted and rejected rows. |
| Malformed row handling | Invalid rows are skipped and written to `logs/rejected_rows.csv` with a source row number and rejection reason. |
| Loading | `src/load_events.py` inserts valid rows into SQLite using `INSERT OR IGNORE` so duplicate `event_id` values do not crash or duplicate data. |
| Transformation | `src/transform_metrics.py` reads from the `events` table and computes session-level metrics. It does not recompute from CSV. |
| Metrics loading | `src/load_metrics.py` upserts metrics into `session_metrics` using `session_token` as the conflict key. |
| API serving | `src/main.py` exposes `GET /sessions`, `GET /sessions/{token}`, and `GET /metrics/summary`. |
| Testing | `tests/` covers validation, event loading idempotency, metric transformation, metric upsert behavior, API responses, pagination validation, 404 behavior, and empty database responses. |

## Design Rationale

| Design choice | Why it was chosen | Tradeoff or consideration |
| --- | --- | --- |
| CSV batch ingestion | The source data is a raw event log export, so a batch CSV reader keeps the pipeline easy to run and inspect locally. | For streaming or near-real-time analytics, this would move to a queue or event bus. |
| Pandas for CSV reading and profiling | Pandas is lightweight enough for this dataset and gives clear support for CSV loading, null checks, duplicate checks, and summary statistics. | For very large files, chunked reads or a distributed processing tool would be safer. |
| Explicit row validation before loading | Invalid data is easier to reason about before it reaches the database. This keeps the `events` table clean and predictable for downstream metrics. | Validation rules need to evolve if the source event schema changes. |
| Log and skip malformed rows | A few bad rows should not stop the entire batch. Rejected rows are kept separately so they can be reviewed without blocking valid data. | In production, rejected rows should be stored with richer metadata and monitored for spikes. |
| SQLite database | SQLite keeps local setup simple and reproducible while still using real relational tables, primary keys, indexes, and SQL queries. | PostgreSQL is a better fit for higher concurrency, larger datasets, and operational controls. |
| Separate `events` and `session_metrics` tables | Raw cleaned events are preserved for auditability, while pre-aggregated session metrics make API reads simple and fast. | Metrics must be refreshed when new events are loaded. |
| Precompute session metrics | The API can serve session analytics without recalculating every metric on each request. This matches the read-heavy serving pattern. | If users need fully real-time metrics, transformation would need to run more frequently or move closer to ingestion. |
| Idempotent loading | `event_id` prevents duplicate event inserts, and `session_token` upserts refresh metrics safely. This makes reruns safe after failures or repeated local testing. | If the same `event_id` arrives with corrected data, a deliberate update strategy would be needed. |
| FastAPI serving layer | FastAPI provides concise route definitions, request validation, response models, and Swagger documentation with minimal setup. | Production deployment would need authentication, rate limiting, and operational monitoring. |

## Repository Structure

```text
USER_ANALYTICS_PIPELINE/
|-- README.md
|-- requirements.txt
|-- data/
|   `-- sample_events.csv
|-- docs/
|   `-- flowchart-drawio.png
|-- sql/
|   `-- schema.sql
|-- src/
|   |-- __init__.py
|   |-- api_schemas.py
|   |-- config.py
|   |-- database.py
|   |-- generate_sample_data.py
|   |-- ingestion.py
|   |-- load_events.py
|   |-- load_metrics.py
|   |-- main.py
|   |-- profile_data.py
|   |-- query_service.py
|   |-- run_ingestion.py
|   |-- run_pipeline.py
|   |-- run_transform.py
|   |-- transform_metrics.py
|   `-- validation.py
`-- tests/
    |-- __init__.py
    |-- test_api.py
    |-- test_load_events.py
    |-- test_load_metrics.py
    |-- test_transform_metrics.py
    `-- test_validation.py
```

## Database Choice

SQLite is used because it is free, lightweight, serverless, and easy to run locally without a separate database server. It is a good fit for this CSV-based batch pipeline because ingestion runs in batches and the API primarily serves read queries over prepared metrics.

For a larger production deployment, PostgreSQL would be the preferred upgrade. It offers stronger concurrency support, better operational tooling, richer indexing options, and more production-ready access control.

## Database Schema

`events` stores cleaned raw event records:

- `event_id` is the primary key and prevents duplicate raw event ingestion.
- `session_token` links events into a user session without storing personal identifiers.
- `event_type`, `timestamp`, `device_type`, and `response_time_ms` keep the fields needed for behavioral metrics.
- `ingested_at` records when SQLite inserted the event.

`session_metrics` stores one aggregate row per session:

- `session_token` is the primary key.
- `total_events` counts valid events in the session.
- `session_duration_seconds` stores the time between first and last event.
- `dominant_device` stores the most frequent device type.
- `average_latency_ms` stores average backend latency.
- `first_event_time` and `last_event_time` support timeline queries.
- `updated_at` changes when a metrics row is refreshed.

Indexes:

- `events(session_token)` speeds up session lookups.
- `events(timestamp)` supports time-based filtering and ordering.
- `events(event_type)` supports event-type breakdowns.
- `session_metrics(average_latency_ms)` supports latency-based filtering and ranking.

## Data Profiling

Run:

```bash
python src/profile_data.py
```

The profiling script reports:

- total row count
- missing values by column
- duplicate `event_id` count
- invalid or negative `response_time_ms` count
- response time summary statistics
- IQR-based latency outlier count
- `event_type` breakdown
- `device_type` breakdown

Very high latency values are profiled as outliers, not automatically rejected.

## Ingestion and Validation

Run ingestion only:

```bash
python src/run_ingestion.py
```

Validation rules:

- Required columns must exist: `event_id`, `session_token`, `event_type`, `timestamp`, `device_type`, and `response_time_ms`.
- `event_id`, `session_token`, and `event_type` must not be empty.
- `timestamp` must be parseable as an ISO 8601 timestamp with timezone information.
- `device_type` must be `mobile`, `desktop`, or `tablet`. Input is accepted case-insensitively and stored in lowercase.
- `response_time_ms` must be an integer greater than or equal to zero.

Malformed rows are skipped instead of crashing the pipeline. Rejected rows are written to `logs/rejected_rows.csv` with a source row number and reason.

Event loading is idempotent because `event_id` is the primary key and `src/load_events.py` uses SQLite `INSERT OR IGNORE`.

## Session Metrics Transformation

Run transformation only after events have been loaded:

```bash
python src/run_transform.py
```

The transformation reads from the `events` table, not directly from CSV.

Aggregation logic:

- `total_events`: count all stored events for the session.
- `first_event_time`: earliest event timestamp.
- `last_event_time`: latest event timestamp.
- `session_duration_seconds`: difference between last and first event in seconds. A one-event session has duration `0`.
- `dominant_device`: most frequent `device_type`; ties are resolved alphabetically.
- `average_latency_ms`: average `response_time_ms`, rounded to two decimal places. Valid high-latency outliers are included.

Metrics loading is idempotent because `session_metrics.session_token` is the primary key and loading uses:

```sql
INSERT ... ON CONFLICT(session_token) DO UPDATE
```

## Full Local Pipeline

Run the complete local flow:

```bash
python src/run_pipeline.py
```

This command:

- initializes the SQLite schema
- ingests and validates `data/sample_events.csv`
- writes rejected rows to `logs/rejected_rows.csv`
- loads valid events into `events`
- transforms session metrics from stored events
- upserts results into `session_metrics`

The command is safe to rerun. Existing events are not duplicated, and session metrics are refreshed.

## API Design and Serving Layer

Prepare data first:

```bash
python src/run_pipeline.py
```

Start the API:

```bash
uvicorn src.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

The project exposes analytics through REST endpoints. FastAPI's Swagger UI is available for local API exploration and testing.

### GET /

Health and endpoint information.

Example response:

```json
{
  "project": "USER_ANALYTICS_PIPELINE",
  "status": "ok",
  "endpoints": [
    "GET /sessions",
    "GET /sessions/{token}",
    "GET /metrics/summary"
  ]
}
```

### GET /sessions

Lists records from `session_metrics`.

Query parameters:

- `page`: default `1`, must be at least `1`.
- `page_size`: default `20`, must be between `1` and `100`.

Example response:

```json
{
  "page": 1,
  "page_size": 20,
  "total_sessions": 36,
  "total_pages": 2,
  "sessions": [
    {
      "session_token": "session_001_hash",
      "total_events": 7,
      "session_duration_seconds": 445.0,
      "dominant_device": "tablet",
      "average_latency_ms": 176.57,
      "first_event_time": "2026-07-01T09:08:00Z",
      "last_event_time": "2026-07-01T09:15:25Z"
    }
  ]
}
```

### GET /sessions/{token}

Retrieves metrics for one `session_token`.

Example response:

```json
{
  "session_token": "session_001_hash",
  "total_events": 7,
  "session_duration_seconds": 445.0,
  "dominant_device": "tablet",
  "average_latency_ms": 176.57,
  "first_event_time": "2026-07-01T09:08:00Z",
  "last_event_time": "2026-07-01T09:15:25Z"
}
```

Missing token response:

```json
{
  "detail": "Session not found: unknown_session"
}
```

### GET /metrics/summary

Returns dataset-wide aggregates from `events` and `session_metrics`.

Example response:

```json
{
  "total_events": 291,
  "average_session_duration_seconds": 448.97,
  "event_type_breakdown": {
    "api_call": 93,
    "button_click": 98,
    "page_view": 100
  },
  "p95_latency_ms": 261.0
}
```

`p95_latency_ms` is calculated in Python from stored `response_time_ms` values using linear interpolation over the sorted latency list. SQLite does not provide a built-in percentile aggregate.

Error handling:

- Missing session token returns `404`.
- Invalid pagination returns `422` through FastAPI request validation.
- Empty database returns clean empty or zero values. `/sessions` returns an empty list, and `/metrics/summary` returns `total_events: 0`, an empty event breakdown, and `p95_latency_ms: null`.

## Testing

Run all tests:

```bash
pytest
```

The tests use temporary SQLite databases where needed, so they do not require a manually created local database.

## Known Assumptions

- Input CSV files follow the expected event log schema.
- Timestamps are expected to include timezone information and are normalized to UTC.
- Very high latency values are treated as valid outliers, not rejected records.
- Duplicate `event_id` rows are ignored to keep ingestion idempotent.
- SQLite is used for local reproducibility.
- The API serves already-prepared data; it does not trigger ingestion or transformation on request.

## Production Considerations

Production orchestration could follow this flow:

![Production pipeline orchestration flowchart](docs/flowchart-drawio.png)

In local development, run the flow manually with:

```bash
python src/run_pipeline.py
```

In production, this could be scheduled using cron, Airflow, GitHub Actions, or a containerized job. Failed runs should be logged and alerted. Idempotency is handled by `event_id` uniqueness in `events` and `session_token` upserts in `session_metrics`.

### Challenges and Future Improvement Considerations

| Area | Potential challenge | Future improvement |
| --- | --- | --- |
| Database scalability | SQLite is simple and reliable for local batch processing, but it is not ideal for many concurrent writers or larger production workloads. | Move to PostgreSQL for stronger concurrency, operational tooling, access control, backups, and richer indexing options. |
| Pipeline observability | The local pipeline prints summaries to the terminal, but production runs need durable logs for debugging and auditability. | Add structured logging, pipeline run IDs, row counts, runtime duration, and success or failure status for each run. |
| Rejected data handling | Rejected rows are written to one CSV file, which is enough locally but can be overwritten or become hard to analyze over time. | Store rejected rows in a dedicated table or timestamped files with error categories, source filename, and pipeline run ID. |
| Schema evolution | A single `schema.sql` file is simple, but production databases need controlled changes over time. | Use migrations so table and index changes can be versioned, reviewed, and rolled back safely. |
| API security | The current API is designed for local use and does not include authentication. | Add authentication, authorization, rate limiting, and request logging before exposing the API outside a trusted environment. |
| Data freshness | The API serves prepared metrics, so stale results are possible if ingestion or transformation fails. | Add freshness checks, last-successful-run metadata, alerts for missed schedules, and dashboard monitoring. |
| Data quality drift | New event types, unexpected devices, or latency spikes could appear as the source system changes. | Add automated data quality checks and alerts for schema drift, volume changes, rejection spikes, and latency outliers. |
| Operational reliability | Scheduled jobs can fail because of missing files, malformed inputs, environment issues, or database locks. | Add retries where safe, clear alerting, failure notifications, and runbooks for investigation. |
