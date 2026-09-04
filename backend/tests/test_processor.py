"""Unit tests for audio validation and pitch-shift processing."""
import io

import librosa
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


def _tone(sr=22050, seconds=1.0, freq=330.0):
    return (0.5 * np.sin(2 * np.pi * freq * np.linspace(0, seconds, int(sr * seconds), endpoint=False))).astype(np.float32)


def test_pitch_shift_separated_disabled_matches_direct(monkeypatch):
    """With separation off, the separated path is identical to direct pitch shift."""
    from audio.config import ProcessingConfig

    sr = 22050
    audio = _tone(sr=sr)
    monkeypatch.setattr(ProcessingConfig, "USE_SEPARATION", False)
    direct = P.pitch_shift(audio, sr, 4)
    assert np.array_equal(P.pitch_shift_separated(audio, sr, 4), direct)


def test_pitch_shift_separated_falls_back_on_error(monkeypatch):
    """If separation raises, fall back to direct pitch shift (same result, right length)."""
    def boom(*args, **kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(P, "get_separator", boom)
    sr = 22050
    audio = _tone(sr=sr)
    direct = P.pitch_shift(audio, sr, 4)
    out = P.pitch_shift_separated(audio, sr, 4)
    assert len(out) == len(audio)
    assert np.array_equal(out, direct)


def _high_band_rms(sig: np.ndarray, lo: int = 12000) -> float:
    """RMS of spectral energy above ``lo`` Hz (a proxy for phase-vocoder aliasing)."""
    S = np.abs(librosa.stft(sig, n_fft=8192, hop_length=1024))
    freqs = np.arange(S.shape[0]) * 44100 / 8192
    return float(np.sqrt(np.mean(np.sum(S[freqs >= lo] ** 2, axis=0))))


def test_down_shift_reduces_high_band_aliasing():
    """A down-shift should suppress the >12 kHz aliasing the phase vocoder adds."""
    sr = 22050
    audio = _tone(sr=sr, freq=330.0)
    out = P.pitch_shift_separated(audio, sr, -6)
    ref = P.pitch_shift(audio, sr, -6)  # same algorithm, no LPF cleanup
    assert _high_band_rms(out) < _high_band_rms(ref)


def test_up_shift_is_not_filtered():
    """Up-shifts keep their real high-frequency content: no LPF is applied."""
    sr = 22050
    audio = _tone(sr=sr, freq=330.0)
    out = P.pitch_shift_separated(audio, sr, 6)
    ref = P.pitch_shift(audio, sr, 6)
    assert np.array_equal(out, ref)


def test_zero_shift_is_identity():
    sr = 22050
    audio = _tone(sr=sr, freq=330.0)
    assert np.array_equal(P.pitch_shift_separated(audio, sr, 0), audio)


def test_pitch_shift_separated_end_to_end(monkeypatch):
    """Full separation + independent pitch-shift pipeline (skips if model can't load)."""
    from audio.config import ProcessingConfig
    monkeypatch.setattr(ProcessingConfig, "USE_SEPARATION", True)  # exercise the split path
    try:
        from audio.separators import get_separator
        get_separator(P.ProcessingConfig.SEPARATION_MODEL)
    except Exception as exc:  # noqa: BLE001 - network/model unavailable is a skip
        import pytest
        pytest.skip(f"demucs model unavailable: {exc}")

    sr = 44100
    audio = _tone(sr=sr, seconds=1.5, freq=440.0)
    out = P.pitch_shift_separated(audio, sr, 5)
    assert out.shape == audio.shape       # channel layout preserved
    assert len(out) == len(audio)         # length preserved
    assert not np.allclose(out, audio)    # pitch actually changed
