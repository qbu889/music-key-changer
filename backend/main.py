"""Music Key Changer — FastAPI backend.

Serves the Apple-style frontend and exposes a synchronous pitch-shift API
(see docs/requirements.md §5 / §8). Files are isolated per session and purged
after 24h.
"""
from __future__ import annotations

import asyncio
import logging
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
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from audio.config import FileConfig, Paths, ErrorCode, FRONTEND_DIR
from audio.processor import AudioError, process, validate

logger = logging.getLogger(__name__)


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


async def _bounded_read(file: UploadFile, limit: int, chunk_size: int = 1 << 20) -> bytes:
    """Read at most ``limit`` bytes from an uploaded file.

    ``UploadFile.read()`` loads the *entire* request body into RAM. An upload
    with a missing or under-reported ``Content-Length`` (chunked / attack
    uploads) can therefore OOM the server even with a ``Content-Length`` check
    in place. This reads in bounded chunks from the underlying spooled file and
    stops at ``limit``, capping memory regardless of what ``Content-Length``
    claims.
    """
    raw = file.file  # SpooledTemporaryFile (binary); read off the event loop
    chunks: list[bytes] = []
    remaining = limit
    while remaining > 0:
        chunk = await asyncio.to_thread(raw.read, min(chunk_size, remaining))
        if not chunk:
            break  # EOF reached before the limit
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


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
    # ``isascii()`` guards against unicode "digit" chars (e.g. '²'): ``isdigit()``
    # is True for them but ``int()`` raises ValueError, which would 500 the request.
    if content_length and content_length.isascii() and content_length.isdigit() and int(content_length) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content={"status": "error", "error_code": ErrorCode.FILE_SIZE_EXCEEDED,
                     "message": f"文件过大，请选择小于 {FileConfig.MAX_FILE_SIZE / 1024 / 1024:.0f}MB 的文件"},
        )
    return await call_next(request)


# --- Security: harden response headers -------------------------------------
# A strict CSP is safe for this app: the only script is the external same-origin
# ./app.js, styles come from ./styles.css, the favicon is a data: URI, and all
# API calls are same-origin. ``blob:`` is permitted so the client-side download
# link (frontend/app.js) works.
CSP_VALUE = (
    "default-src 'self' blob:; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def set_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = CSP_VALUE
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# --- Rate limiting (SlowAPI) -----------------------------------------------
# IP-based rate limiting protects the (optionally GPU-heavy, Demucs-backed)
# processing endpoint from abuse/DoS. In-memory storage suits the MVP
# single-process deployment. The middleware exposes the limiter to rate-limited
# routes via ``request.state.limiter``; routes opt in with ``@limiter.limit``.
# ``headers_enabled`` is intentionally left at its default (False): slowapi
# 0.1.10's success-path header injection passes ``None`` as the response when
# the endpoint returns a plain dict, which raises on *every successful*
# request. We therefore emit Retry-After manually in the 429 handler below
# (best-effort, never breaks the response).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a friendly, structured 429 with a best-effort Retry-After hint."""
    response = JSONResponse(
        status_code=429,
        content={"status": "error", "error_code": "RATE_LIMIT_EXCEEDED",
                 "message": "请求过于频繁，请稍后再试"},
    )
    # ``request.state.view_rate_limit`` = (RateLimitItem, keys) set by slowapi
    # before raising. ``get_window_stats`` -> (hits, remaining, reset_ts) gives
    # the epoch time the hit window resets; Retry-After = seconds from now.
    view = getattr(request.state, "view_rate_limit", None)
    if view:
        item, keys = view
        try:
            reset_ts = main.limiter.limiter.get_window_stats(item, *keys)[-1]
            response.headers["Retry-After"] = str(max(0, int(reset_ts - time.time())))
        except Exception:  # noqa: BLE001 - Retry-After is a hint, never break the 429
            response.headers.setdefault("Retry-After", "60")
    else:
        response.headers.setdefault("Retry-After", "60")
    return response


app.router.limiter = limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)


@app.middleware("http")
async def limit_requests(request: Request, call_next):
    request.state.limiter = limiter
    return await call_next(request)


# --- Health ----------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "formats": sorted(FileConfig.SUPPORTED_EXTS)}


# --- Upload + process (MVP synchronous) ------------------------------------
@app.post("/api/v1/process")
@limiter.limit("5/minute;20/hour")  # IP-based rate limit (SlowAPI)
async def process_audio(request: Request, file: UploadFile = File(...), semitones: int = Form(0)):
    session_id = request.state.session_id
    _sessions[session_id]["process_count"] += 1

    # 0. sanitize the uploaded filename: basename only, reject empty names.
    #    The filename is never written to disk (output uses a random file_id),
    #    but normalizing it strips any path components as defense in depth.
    safe_filename = Path(file.filename).name if file.filename else ""
    if not safe_filename:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error_code": ErrorCode.FILE_FORMAT_INVALID,
                     "message": "缺少上传文件"},
        )

    # 1. read (bounded to cap memory) + validate. ``_bounded_read`` stops at
    #    MAX_UPLOAD_BYTES even when Content-Length is missing/lies, closing the
    #    upload-DoS gap that a Content-Length check alone leaves open.
    data = await _bounded_read(file, MAX_UPLOAD_BYTES)
    if len(data) > FileConfig.MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"status": "error", "error_code": ErrorCode.FILE_SIZE_EXCEEDED,
                     "message": f"文件过大，请选择小于 {FileConfig.MAX_FILE_SIZE / 1024 / 1024:.0f}MB 的文件"},
        )
    try:
        info = validate(safe_filename, data)
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
        result = process(safe_filename, data, semitones)
    except AudioError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error_code": exc.code, "message": exc.message})
    except Exception as exc:  # noqa: BLE001 - unexpected error; log server-side, never leak internals
        logger.error("processing failed for session %s: %r", session_id, exc)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error_code": ErrorCode.UNKNOWN_ERROR,
                     "message": "处理失败，请稍后重试"},
        )

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
