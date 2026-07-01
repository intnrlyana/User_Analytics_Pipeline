from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from src.api_schemas import (
    ErrorResponse,
    MetricsSummaryResponse,
    PaginatedSessionsResponse,
    SessionMetricResponse,
)
from src.database import initialise_database
from src.query_service import (
    calculate_total_pages,
    get_metrics_summary,
    get_session_by_token,
    get_sessions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialise_database()
    yield


app = FastAPI(
    title="User Analytics Pipeline API",
    description="Queryable API for session-level analytics prepared by the local CSV pipeline.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get(
    "/",
    summary="API health and endpoint information",
)
def read_root() -> dict[str, Any]:
    return {
        "project": "USER_ANALYTICS_PIPELINE",
        "status": "ok",
        "endpoints": [
            "GET /sessions",
            "GET /sessions/{token}",
            "GET /metrics/summary",
        ],
    }


@app.get(
    "/sessions",
    response_model=PaginatedSessionsResponse,
    summary="List session metrics",
    description="Returns paginated rows from the session_metrics table.",
)
def read_sessions(
    page: int = Query(default=1, ge=1, description="Page number, starting at 1."),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of sessions per page. Maximum is 100.",
    ),
) -> dict[str, Any]:
    session_page = get_sessions(page=page, page_size=page_size)
    total_sessions = session_page["total_sessions"]

    return {
        "page": page,
        "page_size": page_size,
        "total_sessions": total_sessions,
        "total_pages": calculate_total_pages(total_sessions, page_size),
        "sessions": session_page["sessions"],
    }


@app.get(
    "/sessions/{token}",
    response_model=SessionMetricResponse,
    responses={404: {"model": ErrorResponse, "description": "Session not found"}},
    summary="Get one session metric record",
    description="Returns one row from session_metrics by session_token.",
)
def read_session(token: str) -> dict[str, Any]:
    session = get_session_by_token(token)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {token}",
        )

    return session


@app.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    summary="Get dataset-wide metrics summary",
    description="Returns aggregate metrics calculated from events and session_metrics.",
)
def read_metrics_summary() -> dict[str, Any]:
    return get_metrics_summary()
