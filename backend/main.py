"""Music Key Changer — FastAPI backend.

Serves the Apple-style frontend and exposes a synchronous pitch-shift API
(see docs/requirements.md §5 / §8). Files are isolated per session and purged
after 24h.
"""
from __future__ import annotations

import os
import re
import shutil
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from audio.config import FileConfig, Paths, ErrorCode, FRONTEND_DIR
from audio.processor import AudioError, process, validate


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """Start a daemon thread that purges stale sessions hourly."""
    def _loop():
        while True:
            try:
                _cleanup_expired()
            except Exception:  # noqa: BLE001 - cleanup must never crash the app
                pass
            time.sleep(3600)
    threading.Thread(target=_loop, daemon=True).start()
    yield


app = FastAPI(title="Music Key Changer", version="1.0.0", lifespan=app_lifespan)

# --- Session store (in-memory; fine for MVP) -------------------------------
_sessions: dict[str, dict] = {}


def _user_dir(session_id: str, kind: str) -> Path:
    d = Paths.BASE / session_id / kind
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- Security: session-isolated file access --------------------------------
# A ``file_id`` is always a ``uuid.uuid4().hex`` string -> exactly 32 lowercase
# hex chars. Anything else (``..``, ``/``, ``..%2f`` ...) is rejected outright.
_FILE_ID_RE = re.compile(r"^[a-f0-9]{32}$")


def _resolve_session_file(session_id: str, file_id: str, kind: str) -> Path | None:
    """Resolve a file inside a session's ``kind`` directory.

    Returns ``None`` (treated as "not found") when ``file_id`` is malformed or
    would escape the session directory. This blocks both path traversal
    (``../../etc/passwd``) and cross-session access (IDOR): a file is only
    reachable if it physically lives inside ``<base>/<session_id>/<kind>/``.
    """
    if not _FILE_ID_RE.match(file_id):
        return None
    base = (Paths.BASE / session_id / kind).resolve()
    target = (base / f"{file_id}.wav").resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target


# --- Session middleware: reads/creates the session id and sets the cookie --
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in _sessions:
        session_id = uuid.uuid4().hex
        _sessions[session_id] = {
            "session_id": session_id,
            "upload_count": 0,
            "process_count": 0,
            "created_at": datetime.now(timezone.utc).timestamp(),
            "last_active": datetime.now(timezone.utc).timestamp(),
        }
    request.state.session_id = session_id
    response = await call_next(request)
    # Mark the session as active for TTL accounting.
    _sessions[session_id]["last_active"] = datetime.now(timezone.utc).timestamp()
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme in ("https", "wss"),  # only over TLS
        max_age=Paths.TTL_SECONDS,
    )
    return response


# --- Security: cap upload size before it hits memory (DoS guard) -----------
# ``MAX_FILE_SIZE`` is the file cap; we allow a little extra headroom for the
# multipart envelope. Rejecting on ``Content-Length`` avoids reading a multi-GB
# body into RAM via ``file.read()`` (which otherwise runs *before* validation).
MAX_UPLOAD_BYTES = FileConfig.MAX_FILE_SIZE + 5 * 1024 * 1024


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={"status": "error", "error_code": ErrorCode.FILE_SIZE_EXCEEDED,
                     "message": f"文件过大，请选择小于 {FileConfig.MAX_FILE_SIZE / 1024 / 1024:.0f}MB 的文件"},
        )
    return await call_next(request)


# --- Security: harden response headers -------------------------------------
@app.middleware("http")
async def set_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


# --- Health ----------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "formats": sorted(FileConfig.SUPPORTED_EXTS)}


# --- Upload + process (MVP synchronous) ------------------------------------
@app.post("/api/v1/process")
async def process_audio(request: Request, file: UploadFile = File(...), semitones: int = Form(0)):
    session_id = request.state.session_id
    _sessions[session_id]["process_count"] += 1

    # 1. read + validate synchronously (small enough for MVP)
    data = await file.read()
    try:
        info = validate(file.filename, data)
    except AudioError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error_code": exc.code, "message": exc.message})

    if not (-FileConfig.MAX_SEMITONES <= semitones <= FileConfig.MAX_SEMITONES):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error_code": ErrorCode.FILE_FORMAT_INVALID,
                     "message": f"升降调范围应为 {-FileConfig.MAX_SEMITONES} ~ {FileConfig.MAX_SEMITONES} 半音"},
        )

    # 2. process
    try:
        result = process(file.filename, data, semitones)
    except AudioError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error_code": exc.code, "message": exc.message})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"status": "error", "error_code": ErrorCode.PROCESSING_FAILED, "message": str(exc)})

    # 3. persist result into session-isolated dir
    file_id = uuid.uuid4().hex
    out = _user_dir(session_id, "processed")
    out_path = out / f"{file_id}.wav"
    out_path.write_bytes(result["bytes"])

    return {
        "status": "success",
        "file_id": file_id,
        "info": result["info"],
        "semitones": semitones,
        "output_url": f"/api/v1/download/{file_id}",
    }


@app.get("/api/v1/download/{file_id}")
def download(file_id: str, request: Request):
    session_id = request.state.session_id
    # Reject path traversal / cross-session IDs before touching the filesystem.
    path = _resolve_session_file(session_id, file_id, "processed")
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return FileResponse(str(path), media_type="audio/wav", filename=f"{path.stem}.wav")


@app.get("/api/v1/session/info")
def session_info(request: Request):
    session_id = request.state.session_id
    s = _sessions[session_id]
    return {
        "status": "success",
        "session_id": session_id,
        "process_count": s["process_count"],
    }


@app.delete("/api/v1/session/cleanup")
def session_cleanup(request: Request):
    session_id = request.state.session_id
    root = Paths.BASE / session_id
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    return {"status": "success", "message": "会话文件已清理"}


# --- Periodic cleanup of stale sessions ------------------------------------
def _cleanup_expired() -> int:
    now = datetime.now(timezone.utc).timestamp()
    removed = 0
    if not Paths.BASE.exists():
        return 0
    for session_id in Paths.BASE.iterdir():
        if not session_id.is_dir():
            continue
        last = _sessions.get(session_id.name, {}).get("last_active", 0)
        if now - last > Paths.TTL_SECONDS:
            shutil.rmtree(session_id, ignore_errors=True)
            _sessions.pop(session_id.name, None)  # also drop the in-memory record
            removed += 1
    return removed


# --- Serve the frontend ----------------------------------------------------
FRONTEND = FRONTEND_DIR
if FRONTEND.exists() and FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
    _FRONTEND_READY = True
else:
    _FRONTEND_READY = False


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    if _FRONTEND_READY:
        return FileResponse(str(FRONTEND / "index.html"))
    return HTMLResponse("<h1>Music Key Changer backend</h1><p>frontend/ not found.</p>")
