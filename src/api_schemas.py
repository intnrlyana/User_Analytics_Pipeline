from pydantic import BaseModel


class SessionMetricResponse(BaseModel):
    session_token: str
    total_events: int
    session_duration_seconds: float
    dominant_device: str
    average_latency_ms: float
    first_event_time: str
    last_event_time: str


class PaginatedSessionsResponse(BaseModel):
    page: int
    page_size: int
    total_sessions: int
    total_pages: int
    sessions: list[SessionMetricResponse]


class MetricsSummaryResponse(BaseModel):
    total_events: int
    average_session_duration_seconds: float
    event_type_breakdown: dict[str, int]
    p95_latency_ms: float | None


class ErrorResponse(BaseModel):
    detail: str
