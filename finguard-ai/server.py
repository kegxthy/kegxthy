"""FinGuard API: separate from legacy app.py. Start: uvicorn server:app."""
import os,uuid,asyncio
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from fastapi.responses import FileResponse,Response
from fastapi.middleware.cors import CORSMiddleware
from agent_service import run_agent,report_pdf
app=FastAPI(title="FinGuard AI Agent API",version="0.2")
# Keep CORS restricted; serve UI and API from the same origin.
reports={}
@app.get("/")
def ui():return FileResponse("workspace.html")
@app.get("/health")
def health():return {"status":"ok","model_ready":bool(os.environ.get("LLM_API_KEY"))}
@app.post("/api/reports")
async def create_report(file:UploadFile=File(...),prompt:str=Form("")):
    if not file.filename or not file.filename.lower().endswith((".pdf",".docx")):raise HTTPException(400,"PDF or DOCX required")
    raw=await file.read(12*1024*1024+1)
    if len(raw)>12*1024*1024:raise HTTPException(413,"12 MB limit")
    try: result=await asyncio.wait_for(run_agent(raw,file.filename,prompt),timeout=280)
    except asyncio.TimeoutError:raise HTTPException(504,"Analysis timed out; try a shorter report")
    except Exception as exc:
        # Do not leak API keys, prompts or provider internals to public users.
        if isinstance(exc,ValueError):raise HTTPException(422,str(exc)[:180])
        raise HTTPException(502,"Model or document processing failed; check server logs")
    token=uuid.uuid4().hex
    reports[token]=result
    # Demo-only in-memory storage: clear on restart; cap count.
    if len(reports)>25:reports.pop(next(iter(reports)))
    return {"id":token,**result}
@app.get("/api/reports/{token}/pdf")
def download_report(token:str):
    if token not in reports:raise HTTPException(404,"Report expired or not found")
    try: pdf=report_pdf(reports[token])
    except Exception:raise HTTPException(500,"PDF generation failed")
    return Response(pdf,media_type="application/pdf",headers={"Content-Disposition":'attachment; filename="finguard-risk-report.pdf"'})
