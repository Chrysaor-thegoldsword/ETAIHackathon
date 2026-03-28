from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agents import conversation, doc_extraction, report_generator


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="ET Money Mentor")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

sessions: dict[str, conversation.ConversationSession] = {}


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = ""


class ReportRequest(BaseModel):
    session_id: str


@app.get("/")
async def serve_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest) -> JSONResponse:
    if payload.session_id and payload.session_id in sessions:
        session = sessions[payload.session_id]
    else:
        session = conversation.ConversationSession()
        sessions[session.session_id] = session

    reply, done, analysis, report = session.process_message(payload.message)
    return JSONResponse(
        jsonable_encoder(
            {
            "session_id": session.session_id,
            "response": reply,
            "done": done,
            "progress": session.progress(),
            "analysis": analysis,
            "report": report,
            "profile": session.profile.to_dict(),
            }
        )
    )


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), session_id: str = Form(...)) -> dict[str, Any]:
    if session_id not in sessions:
        return {"error": "Session not found"}

    session = sessions[session_id]
    extracted = await doc_extraction.parse_document(file)
    session.profile.update_profile(extracted)
    session.refresh_analysis()
    return {
        "status": "ok",
        "extracted": extracted,
        "profile": session.profile.to_dict(),
    }


@app.post("/api/report", response_model=None)
async def report_endpoint(payload: ReportRequest):
    if payload.session_id not in sessions:
        return {"error": "Session not found"}

    session = sessions[payload.session_id]
    report = session.report or report_generator.generate_report(session.profile, session.analysis)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        pdf_path = temp_file.name

    report_generator.build_pdf_report(report, pdf_path)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="et_money_mentor_report.pdf",
    )
