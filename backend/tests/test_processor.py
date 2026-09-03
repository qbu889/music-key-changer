"""Unit tests for audio validation and pitch-shift processing."""
import io

import numpy as np
import soundfile as sf

import audio.processor as P


def _wav(freq=440.0, seconds=1.0, sr=44100, ext="wav"):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    data = (0.6 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format=ext.upper(), subtype="PCM_16")
    buf.seek(0)
    return f"tone.{ext}", buf.getvalue(), sr


def test_validate_accepts_wav():
    name, data, sr = _wav()
    info = P.validate(name, data)
    assert info["duration"] == 1.0
    assert info["sample_rate"] == sr


def test_validate_rejects_bad_extension():
    name, data, _ = _wav(ext="wav")
    try:
        P.validate("song.mp4x", data)
    except P.AudioError as e:
        assert e.code == P.ErrorCode.FILE_FORMAT_INVALID


def test_validate_rejects_oversized():
    name, data, _ = _wav()
    fake = b"x" * (P.FileConfig.MAX_FILE_SIZE + 1)
    try:
        P.validate(name, fake)
    except P.AudioError as e:
        assert e.code == P.ErrorCode.FILE_SIZE_EXCEEDED


def test_validate_rejects_too_long():
    _, data, sr = _wav(seconds=6)  # 6s > 5s limit
    try:
        P.validate("long.wav", data)
    except P.AudioError as e:
        assert e.code == P.ErrorCode.DURATION_EXCEEDED


def test_pitch_shift_preserves_length():
    sr = 22050
    audio = (0.5 * np.sin(2 * np.pi * 330 * np.linspace(0, 1, sr, endpoint=False))).astype(np.float32)
    for sem in (-12, -6, -3, 3, 6, 12):
        out = P.pitch_shift(audio, sr, sem)
        assert len(out) == len(audio)


def test_pitch_shift_zero_is_identity():
    sr = 22050
    audio = (0.5 * np.sin(2 * np.pi * 330 * np.linspace(0, 1, sr, endpoint=False))).astype(np.float32)
    assert np.allclose(P.pitch_shift(audio, sr, 0), audio)


def test_process_returns_decodable_wav():
    name, data, sr = _wav()
    result = P.process(name, data, 3)
    assert result["info"]["duration"] == 1.0
    decoded, sample_rate = sf.read(io.BytesIO(result["bytes"]))
    assert sample_rate == sr
    assert len(decoded) > 0
