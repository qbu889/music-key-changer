"""End-to-end API tests using FastAPI's TestClient."""
import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

import main


def _wav_bytes(freq=440.0, seconds=1.0, sr=44100):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    data = (0.6 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


client = TestClient(main.app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_process_and_download_roundtrip():
    payload = _wav_bytes()
    r = client.post(
        "/api/v1/process",
        files={"file": ("tone.wav", payload, "audio/wav")},
        data={"semitones": 3},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert body["semitones"] == 3
    assert body["info"]["duration"] == 1.0

    dl = client.get(f"/api/v1/download/{body['file_id']}")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("audio/wav")
    decoded, sr = sf.read(io.BytesIO(dl.content))
    assert sr == 44100
    assert len(decoded) > 0


def test_process_rejects_bad_extension():
    r = client.post(
        "/api/v1/process",
        files={"file": ("notes.bin", b"not audio", "application/octet-stream")},
        data={"semitones": 2},
    )
    assert r.status_code == 400
    assert r.json()["status"] == "error"
    assert r.json()["error_code"] == "FILE_FORMAT_INVALID"


def test_process_rejects_bad_semitone_range():
    payload = _wav_bytes()
    r = client.post(
        "/api/v1/process",
        files={"file": ("tone.wav", payload, "audio/wav")},
        data={"semitones": 99},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "FILE_FORMAT_INVALID"


def test_download_missing_file_is_404():
    r = client.get("/api/v1/download/does-not-exist")
    assert r.status_code == 404


# --- Security tests --------------------------------------------------------
def test_download_rejects_path_traversal():
    """A file_id with ``..`` must not escape the session directory or read
    arbitrary files on disk."""
    for hostile in ("../../../../etc/passwd", "..", "a" * 31, "a" * 33, "../x", "0x" + "1" * 30):
        r = client.get(f"/api/v1/download/{hostile}")
        assert r.status_code == 404, hostile
        assert b"root:" not in r.content  # never leaked a system file


def test_download_blocks_cross_session_access():
    """A file produced for one session must not be downloadable by another
    session (IDOR protection)."""
    other = TestClient(main.app)  # separate cookie jar -> independent session
    r = other.post(
        "/api/v1/process",
        files={"file": ("tone.wav", _wav_bytes(), "audio/wav")},
        data={"semitones": 2},
    )
    assert r.status_code == 200, r.text
    file_id = r.json()["file_id"]

    # The owning session can still download it.
    ok = other.get(f"/api/v1/download/{file_id}")
    assert ok.status_code == 200

    # A different session cannot (IDOR protection).
    denied = client.get(f"/api/v1/download/{file_id}")
    assert denied.status_code == 404


def test_upload_over_limit_is_rejected():
    """Oversized uploads are rejected (413) before being read into memory."""
    big = b"\x00" * (main.MAX_UPLOAD_BYTES + 1024)
    r = client.post(
        "/api/v1/process",
        files={"file": ("big.wav", big, "audio/wav")},
        data={"semitones": 1},
    )
    assert r.status_code == 413
    assert r.json()["error_code"] == "FILE_SIZE_EXCEEDED"


def test_security_headers_present():
    r = client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_frontend_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "升降调" in r.text
