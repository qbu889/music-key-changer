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

    When ``USE_SEPARATION`` is on, the input is split into vocals / accompaniment
    with Demucs, each track is pitch-shifted independently (this preserves vocal
    clarity that is otherwise lost when pitch-shifting the whole mix at once), then
    re-mixed. If separation fails (e.g. model not downloaded) the pipeline falls
    back to a direct global pitch shift.
    """

    USE_SEPARATION = True
    SEPARATION_MODEL = "mdx_q"          # 2-stem (vocals / accompaniment), ~500MB
    HF_ENDPOINT = "https://hf-mirror.com"  # mirror used when huggingface.co is blocked


class Paths:
    """Session-isolated storage root under <project>/user_data."""

    BASE = PROJECT_ROOT / "user_data"
    TTL_SECONDS = 24 * 3600                      # files expire after 24h
    CLEANUP_MARKER = "cleanup.done"
