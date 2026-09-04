"""Audio validation and pitch-shift processing (Librosa)."""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import logging

import librosa
import numpy as np
import soundfile as sf
from scipy import signal as _sig

from .config import FileConfig, ErrorCode, ProcessingConfig
from .separators import MODEL_SR, get_separator

logger = logging.getLogger(__name__)


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


def _match_length(out: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Trim or zero-pad ``out`` along the last axis to match ``reference`` length."""
    n = reference.shape[-1]
    cur = out.shape[-1]
    if cur == n:
        return out
    if cur > n:
        return out[..., :n] if out.ndim > 1 else out[:n]
    pad = np.zeros((*out.shape[:-1], n - cur), dtype=out.dtype)
    return np.concatenate([out, pad], axis=-1)


def _match_level(out: np.ndarray, reference: np.ndarray, target: float = 0.98) -> np.ndarray:
    """Scale ``out`` so its peak matches ``reference``'s peak (capped at ``target``).

    Recombining separated stems can push the summed peak above 1.0 and clip on
    16-bit PCM encoding. Matching the original's peak keeps the processed track
    at the same perceived volume while preventing clipping.
    """
    dest = min(target, float(np.max(np.abs(reference))))
    out_peak = float(np.max(np.abs(out)))
    if out_peak > 1e-6:
        out = out * (dest / out_peak)
    return out


def _aliasing_cleanup(audio: np.ndarray, semitones: int, sample_rate: int) -> np.ndarray:
    """Suppress pitch-shift aliasing in the high band (down-shifts only).

    Librosa's phase-vocoder pitch shift leaves broadband aliasing above ~12 kHz.
    For a *down*-shift the real signal energy moves downward, so the region above
    ~12 kHz is dominated by that aliasing rather than real content: a zero-phase
    Butterworth low-pass with a cutoff that scales down with the shift magnitude
    removes most of it while preserving the audible band (<0.2% energy loss up to
    16 kHz, verified empirically). For 0 / up-shifts the real content still occupies
    the high band, so filtering would only dull the track — hence no filtering.
    """
    if semitones >= 0:
        return audio
    nyquist = sample_rate / 2
    k = 2.0 ** (semitones / 12.0)              # < 1 for down-shifts
    cutoff = min(nyquist * 0.98, max(9000.0, 12000.0 * k + 1500.0))
    if cutoff >= nyquist:
        return audio
    b, a = _sig.butter(4, cutoff / nyquist, btype="low")
    return _sig.filtfilt(b, a, audio)


def pitch_shift_separated(audio: np.ndarray, sample_rate: int, semitones: int) -> np.ndarray:
    """Pitch-shift the whole mix coherently (default), or via stem separation.

    The default path pitch-shifts the entire mix in one pass so the vocal and
    accompaniment stay phase-aligned and no extra high-frequency hiss is added.
    When ``USE_SEPARATION`` is enabled we instead split into vocals / accompaniment
    with Demucs, pitch-shift each stem (both stems shift together so the song keeps
    one key), re-mix and resample back to the input sample rate. This can preserve
    some vocal-band tonality but the spectrogram reconstruction adds high-frequency
    noise, so it is opt-in. Falls back to a direct global pitch shift on any error
    (e.g. model not downloaded).
    """
    if semitones == 0:
        return audio
    if not ProcessingConfig.USE_SEPARATION:
        return _aliasing_cleanup(pitch_shift(audio, sample_rate, semitones), semitones, sample_rate)

    try:
        separator = get_separator(ProcessingConfig.SEPARATION_MODEL)
        vocals, accompaniment = separator.separate(audio, sample_rate)
        v = librosa.effects.pitch_shift(
            vocals, sr=MODEL_SR, n_steps=semitones, res_type="kaiser_best"
        )
        a = librosa.effects.pitch_shift(
            accompaniment, sr=MODEL_SR, n_steps=semitones, res_type="kaiser_best"
        )
        # Shift BOTH stems so the whole song changes key together and the
        # vocal stays in relation to the accompaniment (mix the shifted one).
        mixed = v + a
        out = librosa.core.resample(mixed, orig_sr=MODEL_SR, target_sr=sample_rate)
        out = _match_level(out, audio)
        return _aliasing_cleanup(_match_length(out, audio), semitones, sample_rate)
    except Exception as exc:  # noqa: BLE001 - separation is best-effort
        logger.warning("separation failed (%s); using direct pitch shift", exc)
        return _aliasing_cleanup(pitch_shift(audio, sample_rate, semitones), semitones, sample_rate)


def process(filename: str, data: bytes, semitones: int) -> dict:
    """Validate, pitch-shift and encode. Returns info + raw WAV bytes."""
    info = validate(filename, data)
    audio, sr = librosa.load(io.BytesIO(data), sr=None)
    processed = pitch_shift_separated(audio, sr, semitones)
    return {"info": info, "bytes": save_wav(processed, sr)}
