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


def test_frontend_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "升降调" in r.text
