"""Acoustic feature extraction.

`extract_features` turns raw audio into an :class:`AcousticFeatures`. It uses
librosa when available; otherwise it raises so callers fall back to the
pre-baked features attached to mock scenario turns.
"""
from __future__ import annotations

import numpy as np

from ..schemas import AcousticFeatures

try:  # optional dependency
    import librosa  # type: ignore

    _HAS_LIBROSA = True
except Exception:  # pragma: no cover - optional
    _HAS_LIBROSA = False


def librosa_available() -> bool:
    return _HAS_LIBROSA


def extract_features(samples: np.ndarray, sr: int) -> AcousticFeatures:
    """Extract a compact acoustic fingerprint from a mono waveform.

    Raises RuntimeError if librosa is not installed.
    """
    if not _HAS_LIBROSA:
        raise RuntimeError("librosa not installed; cannot extract live features")

    samples = samples.astype(np.float32)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if np.max(np.abs(samples)) > 0:
        samples = samples / np.max(np.abs(samples))

    # Fundamental frequency track (voiced frames only).
    f0, voiced, _ = librosa.pyin(
        samples,
        fmin=float(librosa.note_to_hz("C2")),
        fmax=float(librosa.note_to_hz("C6")),
        sr=sr,
    )
    f0v = f0[~np.isnan(f0)]
    f0_std = float(np.std(f0v)) if f0v.size else 0.0
    # Jitter: mean relative period difference.
    if f0v.size > 2:
        periods = 1.0 / np.clip(f0v, 1e-6, None)
        jitter = float(np.mean(np.abs(np.diff(periods))) / np.mean(periods))
    else:
        jitter = 0.0

    rms = librosa.feature.rms(y=samples)[0]
    shimmer = float(np.mean(np.abs(np.diff(rms))) / (np.mean(rms) + 1e-9))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=samples)))

    # Harmonics-to-noise ratio via harmonic/percussive separation.
    harm, perc = librosa.effects.hpss(samples)
    hnr = 10.0 * np.log10((np.mean(harm**2) + 1e-9) / (np.mean(perc**2) + 1e-9))

    silence = float(np.mean(rms < (0.15 * np.mean(rms) + 1e-9)))

    return AcousticFeatures(
        jitter=round(jitter, 4),
        shimmer=round(shimmer, 4),
        spectral_flatness=round(flatness, 4),
        hnr=round(float(hnr), 2),
        f0_std=round(f0_std, 2),
        silence_ratio=round(silence, 3),
    )
