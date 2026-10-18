"""FinGuard V1 single-team workspace. Run one Uvicorn worker."""

import asyncio
import hmac
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, Response, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from finance import Figure, verify
from task_store import Store, now
from export_pdf import report_pdf
import workflow

store = None
jobs = set()
WARNINGS = [
    "Screening thresholds are illustrative and sector-dependent; signals are not conclusions.",
    "OCR is unavailable. PDF tables and XLSX cached formulas may be incomplete.",
    "A matching quote does not establish table semantics. Confirm period, units and consolidated scope.",
    "Model observations are interpretation, not independently verified facts.",
]


@asynccontextmanager
async def lifespan(app):
    global store
    store = Store()
    for task in store.all():
        if task["status"] in ("extracting", "analyzing"):
            task["status"] = "failed"
            task["error"] = "Server restarted during execution. Create a new task."
            store.save(task)
    yield
    for job in list(jobs):
        job.cancel()
    await asyncio.gather(*jobs, return_exceptions=True)


app = FastAPI(title="FinGuard AI", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def access(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        token = os.getenv("FINGUARD_ACCESS_TOKEN")
        if token:
            if not hmac.compare_digest(
                request.headers.get("authorization", ""), "Bearer " + token
            ):
                return JSONResponse(
                    {"detail": "Workspace token required"}, status_code=401
                )
        elif request.client and request.client.host not in (
            "127.0.0.1",
            "::1",
            "testclient",
        ):
            return JSONResponse(
                {"detail": "Remote access requires FINGUARD_ACCESS_TOKEN"},
                status_code=403,
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
    )
    return response


def get(token):
    task = store.get(token)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


def launch(coro):
    job = asyncio.create_task(coro)
    jobs.add(job)
    job.add_done_callback(jobs.discard)


async def event(token, message):
    task = get(token)
    task["events"].append({"at": now(), "message": message})
    store.save(task)


async def execute(token, action):
    try:
        async with asyncio.timeout(600):
            task = get(token)
            if action == "extract":
                figures, warnings = await workflow.extract_figures(
                    task["sources"], lambda m: event(token, m)
                )
                task = get(token)
                task["figures"] = figures
                task["warnings"] += warnings
                task["status"] = "needs_review"
            else:
                result = await workflow.agent(
                    task["figures"], task["focus"], lambda m: event(token, m)
                )
                task = get(token)
                task["result"] = result
                task["status"] = "completed"
            store.save(task)
            await event(token, task["status"])
    except asyncio.CancelledError:
        task = get(token)
        task["status"] = "failed"
        task["error"] = "Execution interrupted"
        store.save(task)
        raise
    except Exception:
        task = get(token)
        task["status"] = "failed"
        task["error"] = (
            "Processing failed or timed out. Check model configuration and document; retry with a new task."
        )
        store.save(task)
        await event(token, "failed")


@app.get("/")
def ui():
    return FileResponse(Path(__file__).with_name("workspace.html"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_ready": bool(os.getenv("LLM_API_KEY")),
        "storage": "sqlite",
        "remote_access_ready": bool(os.getenv("FINGUARD_ACCESS_TOKEN")),
    }


@app.get("/api/tasks")
def history():
    return [
        {
            "id": t["id"],
            "filename": t["filename"],
            "status": t["status"],
            "updated_at": t["updated_at"],
        }
        for t in store.all()
    ]


@app.get("/api/tasks/{token}")
def detail(token: str):
    return get(token)


@app.post("/api/reports", status_code=202)
@app.post("/api/tasks", status_code=202)
async def create(
    file: UploadFile = File(...),
    focus: str = Form("", max_length=2000),
    prompt: str = Form("", max_length=2000),
    provider_consent: bool = Form(False),
):
    if not provider_consent:
        raise HTTPException(
            422, "Explicit approval to send document to DeepSeek is required"
        )
    if not os.getenv("LLM_API_KEY"):
        raise HTTPException(503, "Server LLM_API_KEY is not configured")
    if len(jobs) >= 2:
        raise HTTPException(429, "Workspace execution capacity reached")
    if len(store.all()) >= 100:
        raise HTTPException(429, "Delete old tasks; maximum 100 stored tasks")
    name = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1][:200]
    if Path(name).suffix.lower() not in (".pdf", ".docx", ".xlsx"):
        raise HTTPException(415, "PDF, DOCX or XLSX required")
    raw = await file.read(12 * 1024 * 1024 + 1)
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "12 MB limit")
    try:
        sources = await asyncio.to_thread(workflow.extract, raw, name)
    except Exception:
        raise HTTPException(
            422,
            "Invalid, encrypted, oversized or non-text document. OCR is unavailable.",
        )
    if len(jobs) >= 2:
        raise HTTPException(429, "Workspace execution capacity reached")
    token = uuid.uuid4().hex
    task = {
        "id": token,
        "filename": name,
        "focus": (focus or prompt)[:2000],
        "sources": sources,
        "figures": [],
        "warnings": list(WARNINGS),
        "status": "extracting",
        "events": [],
        "created_at": now(),
        "provider_consent_at": now(),
        "error": None,
        "result": None,
    }
    store.save(task)
    await event(token, "ingestion completed; extraction queued")
    launch(execute(token, "extract"))
    return task


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    figures: list[Figure] = Field(max_length=8)


@app.post("/api/tasks/{token}/confirm", status_code=202)
async def confirm(token: str, body: Confirmation):
    task = get(token)
    if task["status"] != "needs_review":
        raise HTTPException(409, "Task is not awaiting confirmation")
    if len(jobs) >= 2:
        raise HTTPException(429, "Workspace execution capacity reached")
    figures = [f.model_dump() for f in body.figures]
    if not figures:
        raise HTTPException(422, "At least one source-backed figure is required")
    if len({f["field"] for f in figures}) != len(figures):
        raise HTTPException(422, "Select one period and one figure per field")
    valid, bad = verify(figures, task["sources"])
    if bad:
        raise HTTPException(
            422, "Corrections must have a matching source quote and number"
        )
    if len({(f["period"], f["currency"]) for f in valid}) != 1:
        raise HTTPException(422, "Use a single fiscal period and currency")
    task["figures"] = valid
    task["confirmed_at"] = now()
    task["status"] = "analyzing"
    store.save(task)
    await event(token, "user confirmed figures; deterministic analysis queued")
    launch(execute(token, "analyze"))
    return task


@app.delete("/api/tasks/{token}", status_code=204)
def delete(token: str):
    if get(token)["status"] in ("extracting", "analyzing"):
        raise HTTPException(409, "Wait for execution to finish")
    store.delete(token)
    return Response(status_code=204)


@app.get("/api/reports/{token}/pdf")
@app.get("/api/tasks/{token}/pdf")
def pdf(token: str):
    task = get(token)
    if task["status"] != "completed":
        raise HTTPException(409, "Report is not completed")
    return Response(
        report_pdf(task),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="finguard-report.pdf"'},
    )
