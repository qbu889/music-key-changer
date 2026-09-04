"""Central configuration: limits, supported formats, paths and error codes."""
from __future__ import annotations

from pathlib import Path

# config.py lives at backend/audio/config.py -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


class FileConfig:
    """Upload constraints (see docs/requirements.md §3.2.1 / §4)."""

    MAX_FILE_SIZE = 50 * 1024 * 1024          # 50 MB
    MAX_DURATION = 600                         # 10 minutes, in seconds
    MAX_SEMITONES = 12
    MIN_SEMITONES = -12

    SUPPORTED_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".mp4"}
    # MIME types browsers may send for the above extensions.
    SUPPORTED_MIME = {
        "audio/mpeg", "audio/mp3", "audio/x-wav", "audio/wav", "audio/flac",
        "audio/aac", "audio/ogg", "audio/mp4", "audio/x-m4a", "application/mp4",
    }


class ErrorCode:
    FILE_FORMAT_INVALID = "FILE_FORMAT_INVALID"
    FILE_SIZE_EXCEEDED = "FILE_SIZE_EXCEEDED"
    DURATION_EXCEEDED = "DURATION_EXCEEDED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ProcessingConfig:
    """Controls the pitch-shift pipeline.

    ``USE_SEPARATION`` defaults to ``False``: the whole mix is pitch-shifted in one
    coherent pass, which keeps vocal/accompaniment phase alignment and adds no extra
    high-frequency hiss. Splitting into stems with Demucs first (``True``) preserves
    some vocal-band tonality but the spectrogram reconstruction adds noticeable
    high-frequency "electric" noise and stem re-mixing breaks phase coherence
    (comb-filtering), so it is offered only as an opt-in. If separation fails
    (e.g. model not downloaded) the pipeline falls back to a direct global pitch shift.
    """

    USE_SEPARATION = False
    SEPARATION_MODEL = "mdx_q"          # 2-stem (vocals / accompaniment), ~500MB
    HF_ENDPOINT = "https://hf-mirror.com"  # mirror used when huggingface.co is blocked


class Paths:
    """Session-isolated storage root under <project>/user_data."""

    BASE = PROJECT_ROOT / "user_data"
    TTL_SECONDS = 24 * 3600                      # files expire after 24h
    CLEANUP_MARKER = "cleanup.done"
