"""Audio validation and pitch-shift processing (Librosa)."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from .config import FileConfig, ErrorCode


class AudioError(Exception):
    """Raised for user-facing, validated errors (carries an ErrorCode)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class AudioInfo:
    duration: float
    sample_rate: int
    channels: int


def _validate_metadata(filename: str, data: bytes) -> None:
    """Check extension, size and MIME-independence before touching audio."""
    ext = Path(filename).suffix.lower()
    if ext not in FileConfig.SUPPORTED_EXTS:
        raise AudioError(
            ErrorCode.FILE_FORMAT_INVALID,
            f"不支持的格式：{ext or '未知'}，请选择 MP3 / WAV / FLAC / AAC / OGG",
        )
    if len(data) > FileConfig.MAX_FILE_SIZE:
        raise AudioError(
            ErrorCode.FILE_SIZE_EXCEEDED,
            f"文件大小超过限制：{len(data) / 1024 / 1024:.1f}MB > 50MB",
        )


def get_info(filename: str, data: bytes) -> AudioInfo:
    """Return duration / sample rate / channels, validating first."""
    _validate_metadata(filename, data)
    audio, sr = librosa.load(io.BytesIO(data), sr=None)
    channels = 1 if audio.ndim == 1 else audio.shape[1]
    return AudioInfo(duration=float(len(audio) / sr), sample_rate=int(sr), channels=channels)


def validate(filename: str, data: bytes) -> dict:
    """Public validation helper returning a serialisable info dict."""
    info = get_info(filename, data)
    if info.duration > FileConfig.MAX_DURATION:
        raise AudioError(
            ErrorCode.DURATION_EXCEEDED,
            f"音频时长超过限制：{info.duration:.1f}s > {FileConfig.MAX_DURATION}s",
        )
    return {
        "duration": round(info.duration, 3),
        "sample_rate": info.sample_rate,
        "channels": info.channels,
    }


def pitch_shift(audio: np.ndarray, sample_rate: int, semitones: int) -> np.ndarray:
    """Shift pitch by ``semitones`` (-12..12), preserving tempo & length.

    Uses Librosa's time-domain pitch shift (res_type='kaiser_best' for quality).
    """
    if not (-FileConfig.MAX_SEMITONES <= semitones <= FileConfig.MAX_SEMITONES):
        raise AudioError(
            ErrorCode.FILE_FORMAT_INVALID,
            f"升降调范围应为 {-FileConfig.MAX_SEMITONES} ~ {FileConfig.MAX_SEMITONES} 半音",
        )
    if semitones == 0:
        return audio
    return librosa.effects.pitch_shift(
        audio, sr=sample_rate, n_steps=semitones, res_type="kaiser_best"
    )


def save_wav(audio: np.ndarray, sample_rate: int) -> bytes:
    """Encode processed audio to a WAV blob in memory."""
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def process(filename: str, data: bytes, semitones: int) -> dict:
    """Validate, pitch-shift and encode. Returns info + raw WAV bytes."""
    info = validate(filename, data)
    audio, sr = librosa.load(io.BytesIO(data), sr=None)
    processed = pitch_shift(audio, sr, semitones)
    return {"info": info, "bytes": save_wav(processed, sr)}
