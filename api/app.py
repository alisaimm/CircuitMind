import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional
import json
import time

from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("circuitmind")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CircuitMind API",
    description="AI-powered circuit generator, explainer, and diagnostics tool",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Request logging middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response

# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please try again."},
    )

# ── Input models ───────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        if len(v) > 1000:
            raise ValueError("prompt must be under 1000 characters")
        return v.strip()


class CircuitRequest(BaseModel):
    circuit_json: dict


class ExportRequest(BaseModel):
    circuit_json: dict
    export_format: Optional[str] = "spice"

    @field_validator("export_format")
    @classmethod
    def valid_format(cls, v: str) -> str:
        allowed = {"spice", "svg", "gate_json"}
        if v not in allowed:
            raise ValueError(f"export_format must be one of {allowed}")
        return v


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {
        "status": "running",
        "message": "CircuitMind API is live!",
        "version": "1.0.0",
        "endpoints": {
            "generate":             "POST /generate",
            "explain":              "POST /explain",
            "diagnose":             "POST /diagnose",
            "export":               "POST /export",
            "generate_and_explain": "POST /generate-and-explain",
        },
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# ── Core endpoints ─────────────────────────────────────────────────────────────
@app.post("/generate", tags=["core"])
def generate(req: GenerateRequest):
    """Convert a natural language prompt into circuit JSON."""
    logger.info(f"Generate request: '{req.prompt[:60]}'")
    result = generate_circuit(req.prompt)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.post("/explain", tags=["core"])
def explain(req: CircuitRequest):
    """Explain a circuit in plain English."""
    logger.info("Explain request received")
    result = explain_circuit(req.circuit_json)
    return result


@app.post("/diagnose", tags=["core"])
def diagnose(req: CircuitRequest):
    """Check a circuit for electrical issues."""
    logger.info("Diagnose request received")
    result = diagnose_circuit(req.circuit_json)
    return result


@app.post("/export", tags=["core"])
def export(req: ExportRequest):
    """Export a circuit to SPICE netlist, SVG, or gate JSON."""
    logger.info(f"Export request: format={req.export_format}")
    json_str = json.dumps(req.circuit_json)
    result = export_module(json_str, export_format=req.export_format)
    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@app.post("/generate-and-explain", tags=["core"])
def generate_and_explain(req: GenerateRequest):
    """Generate a circuit, then explain and diagnose it in one request."""
    logger.info(f"Generate-and-explain request: '{req.prompt[:60]}'")
    circuit = generate_circuit(req.prompt)
    if "error" in circuit:
        raise HTTPException(status_code=422, detail=circuit["error"])
    return {
        "circuit":     circuit,
        "explanation": explain_circuit(circuit),
        "diagnosis":   diagnose_circuit(circuit),
    }
