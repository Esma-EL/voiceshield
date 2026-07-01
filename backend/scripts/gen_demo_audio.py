"""Generate two example WAV files for the /api/analyze/audio endpoint:

    demo_audio/human.wav      - jittery, harmonically rich -> scores "human"
    demo_audio/synthetic.wav  - flat pitch, vocoder-buzzy -> scores "synthetic"

These are crude synthesized signals (not real speech) — just enough to exercise
the live acoustic-feature path end-to-end. Real call audio replaces them later.

    python scripts/gen_demo_audio.py     (needs numpy + soundfile)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

SR = 16_000
DUR = 2.5
OUT = Path(__file__).resolve().parent.parent / "demo_audio"


def _save(name: str, sig: np.ndarray) -> None:
    OUT.mkdir(exist_ok=True)
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.9
    try:
        import soundfile as sf  # type: ignore
        sf.write(OUT / name, sig.astype(np.float32), SR)
    except Exception:
        # Fallback: write a 16-bit PCM WAV with the stdlib.
        import wave
        pcm = (sig * 32767).astype(np.int16)
        with wave.open(str(OUT / name), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
    print(f"wrote {OUT / name}")


def human() -> np.ndarray:
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    # Wandering pitch (natural prosody) + jitter + several harmonics.
    f0 = 130 + 25 * np.sin(2 * np.pi * 0.7 * t) + np.random.randn(t.size) * 3
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = sum((1.0 / k) * np.sin(k * phase) for k in range(1, 7))
    sig *= (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3 * t)))  # amplitude shimmer
    sig += 0.02 * np.random.randn(t.size)                    # breath noise
    return sig


def synthetic() -> np.ndarray:
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    # Rock-steady pitch, buzzy spectrum, with spliced micro-silences.
    f0 = np.full(t.size, 145.0)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    sig = np.sign(np.sin(phase)) * 0.6 + 0.4 * np.sin(phase)  # vocoder buzz
    for start in (0.5, 1.1, 1.7):                              # splice gaps
        i = int(start * SR)
        sig[i:i + int(0.03 * SR)] = 0.0
    return sig


if __name__ == "__main__":
    np.random.seed(7)
    _save("human.wav", human())
    _save("synthetic.wav", synthetic())
