CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    session_token TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    device_type TEXT NOT NULL,
    response_time_ms INTEGER NOT NULL,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_metrics (
    session_token TEXT PRIMARY KEY,
    total_events INTEGER NOT NULL,
    session_duration_seconds REAL NOT NULL,
    dominant_device TEXT NOT NULL,
    average_latency_ms REAL NOT NULL,
    first_event_time TEXT NOT NULL,
    last_event_time TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_session_token
    ON events(session_token);

CREATE INDEX IF NOT EXISTS idx_events_timestamp
    ON events(timestamp);

CREATE INDEX IF NOT EXISTS idx_events_event_type
    ON events(event_type);

CREATE INDEX IF NOT EXISTS idx_session_metrics_average_latency_ms
    ON session_metrics(average_latency_ms);
