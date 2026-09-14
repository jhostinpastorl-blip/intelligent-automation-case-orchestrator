import os

import redis
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import get_engine
from app.models import AuditEvent, CaseCreate, CaseView, Metrics
from app.security import ApiKeyMiddleware
from app.service import CaseService
from app.store import store
from app.telemetry import configure_telemetry

app = FastAPI(
    title="Intelligent Automation Case Orchestrator",
    version="1.0.0",
    description="Guarded LLM workflow with function calling, HITL, SQL persistence and controlled tools.",
)
app.add_middleware(ApiKeyMiddleware)
configure_telemetry(app)
service = CaseService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready():
    dependencies = {}
    healthy = True

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        dependencies["database"] = "ok"
    except Exception:  # noqa: BLE001 - readiness must degrade safely for any dependency failure
        dependencies["database"] = "unavailable"
        healthy = False

    if os.getenv("DISPATCH_BACKEND", "database").lower() == "redis":
        try:
            redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                socket_connect_timeout=1,
            ).ping()
            dependencies["redis"] = "ok"
        except Exception:  # noqa: BLE001 - readiness must degrade safely for any dependency failure
            dependencies["redis"] = "unavailable"
            healthy = False

    payload = {
        "status": "ready" if healthy else "not_ready",
        "dependencies": dependencies,
    }
    if healthy:
        return payload
    return JSONResponse(status_code=503, content=payload)


@app.post("/cases", response_model=CaseView, status_code=status.HTTP_201_CREATED)
def create_case(request: CaseCreate) -> CaseView:
    return service.create(request)


@app.get("/cases/{case_id}", response_model=CaseView)
def get_case(case_id: str) -> CaseView:
    result = service.get(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


@app.post("/cases/{case_id}/analyze", response_model=CaseView)
def analyze_case(case_id: str) -> CaseView:
    try:
        return service.analyze(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc


@app.post("/cases/{case_id}/approve", response_model=CaseView)
def approve_case(case_id: str) -> CaseView:
    try:
        return service.approve(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/cases/{case_id}/execute", response_model=CaseView, status_code=status.HTTP_202_ACCEPTED)
def execute_case(case_id: str) -> CaseView:
    try:
        return service.execute(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/cases/{case_id}/audit", response_model=list[AuditEvent])
def audit(case_id: str) -> list[AuditEvent]:
    try:
        return service.audit(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc


@app.get("/metrics", response_model=Metrics)
def metrics() -> Metrics:
    return store.metrics()
