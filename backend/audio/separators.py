"""Vocal / accompaniment separation via Demucs.

Lazy-loaded and cached so the model is only fetched once and only when
separation is actually used.

Network note
------------
Demucs 4.x fetches its weights through ``torch.hub`` from a HuggingFace
``safetensors`` URL, and torch.hub ignores the ``HF_ENDPOINT`` mirror env var.
When HuggingFace is unreachable (common in mainland-China networks) we
transparently route those URLs through ``hf-mirror.com``. Set
``DEMUCS_HF_MIRROR=0`` to disable this behaviour.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

import numpy as np

# Point huggingface-hub (used by demucs for config metadata) at a mirror BEFORE
# demucs/torch import. No-op if the environment already sets HF_ENDPOINT.
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# NOTE: torch is intentionally NOT imported here. It is imported lazily inside
# SourceSeparator methods so the default (non-separation) pipeline stays light.

# Demucs models are trained at this sample rate; we resample in/out around it.
MODEL_SR = 44100
_MIRROR_HOST = "hf-mirror.com"


def _enable_hf_mirror() -> bool:
    """Route torch.hub's HuggingFace weight URLs through hf-mirror.com.

    torch.hub performs its own HEAD + download and ignores HF_ENDPOINT, so we
    patch ``load_state_dict_from_url`` to rewrite the host up front. Disabled by
    ``DEMUCS_HF_MIRROR=0``.
    """
    if os.environ.get("DEMUCS_HF_MIRROR", "1").lower() in ("0", "false", "no"):
        return False
    try:
        import torch.hub as _th
    except Exception:
        return False

    orig = _th.load_state_dict_from_url
    if getattr(orig, "_mkc_mirror_patched", False):
        return True

    def patched(url, *args, **kwargs):
        if "huggingface.co" in url or "hf.co" in url:
            url = re.sub(
                r"https?://(?:www\.)?(?:hf\.co|huggingface\.co)",
                f"https://{_MIRROR_HOST}",
                url,
            )
        return orig(url, *args, **kwargs)

    patched._mkc_mirror_patched = True  # type: ignore[attr-defined]
    _th.load_state_dict_from_url = patched  # type: ignore[assignment]
    return True


class SourceSeparator:
    """Separates a numpy audio array into (vocals, accompaniment).

    ``audio`` may be 1D (mono) or 2D (channels, samples) at ``orig_sr``.
    Returns ``(vocals, accompaniment)`` as numpy arrays at ``MODEL_SR`` with the
    same channel layout as the input.
    """

    def __init__(self, model_name: str = "mdx_q"):
        from demucs.pretrained import get_model  # lazy: avoids importing torch/
        # demucs unless separation is used (keeps the fallback path lightweight)

        self.model_name = model_name
        self.device = self._pick_device()
        self.model = get_model(model_name)
        self.model.to(self.device)
        self.model.eval()
        self.sources = list(getattr(self.model, "sources", []))

    @staticmethod
    def _pick_device() -> torch.device:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    def _to_tensor(self, audio: np.ndarray, orig_sr: int) -> torch.Tensor:
        import librosa
        import torch

        if audio.ndim == 1:
            # Demucs models expect stereo input; upmix mono -> stereo.
            resampled = librosa.core.resample(audio, orig_sr=orig_sr, target_sr=MODEL_SR)
            return torch.from_numpy(np.stack([resampled, resampled], axis=0))[None].contiguous()  # (1,2,T)
        channels = [
            librosa.core.resample(audio[c], orig_sr=orig_sr, target_sr=MODEL_SR)
            for c in range(audio.shape[0])
        ]
        return torch.from_numpy(np.stack(channels, axis=0))[None].contiguous()  # (1,C,T)

    def _run_model(self, x: torch.Tensor) -> torch.Tensor:
        """Run the model via ``apply_model`` (handles both HDemucs and
        BagOfModels, with overlap-add refinement for cleaner separation)."""
        import torch
        from demucs.apply import apply_model

        with torch.no_grad():
            try:
                return apply_model(self.model, x)
            except RuntimeError:
                # Some ops may not be available on the chosen device (e.g. MPS);
                # fall back to CPU transparently.
                self.model = self.model.to("cpu")
                self.device = torch.device("cpu")
                return apply_model(self.model, x.to("cpu"))

    def separate(self, audio: np.ndarray, orig_sr: int):
        mono_in = audio.ndim == 1
        x = self._to_tensor(audio, orig_sr).to(self.device).float()
        # apply_model returns (batch, sources, channels, samples)
        sources = self._run_model(x)
        sources = sources.detach().cpu().numpy()
        if sources.ndim == 4:
            sources = sources[0]  # drop batch dim -> (S, C, T)

        names = self.sources
        v_idx = names.index("vocals") if "vocals" in names else 0
        acc_idx = [i for i in range(len(names)) if i != v_idx]
        vocals = sources[v_idx]
        accompaniment = sources[acc_idx].sum(axis=0) if acc_idx else np.zeros_like(sources[0])
        if mono_in:  # preserve the input's channel layout
            vocals = vocals.mean(axis=0)
            accompaniment = accompaniment.mean(axis=0)
        return vocals, accompaniment


@lru_cache(maxsize=1)
def get_separator(model_name: str = "mdx_q") -> SourceSeparator:
    """Return a cached ``SourceSeparator`` (created on first call)."""
    _enable_hf_mirror()
    return SourceSeparator(model_name)
