"""
FastAPI REST API Server for Winter Formula Acid Base.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from winter_acid_base import calculate_metrics
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Winter Formula Acid Base API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class CalculationRequest(BaseModel):
    hco3: float
    pco2: float | None = None
    sodium: float | None = None
    chloride: float | None = None
    albumin: float | None = None


@app.post("/api/calculate")
def api_calculate(payload: CalculationRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "winter-formula-acid-base"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "running"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Mount last so API routes take priority; same UI works on Pages and locally.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True), name="web")
