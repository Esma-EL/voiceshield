"""Voice anti-spoofing detector.

Two engines, selected at runtime:

* ``model``     - a HuggingFace/ModelScope audio-classification model
                  (e.g. an AASIST / wav2vec2 anti-spoofing checkpoint). Used
                  only if ``SPOOFING_MODEL_ID`` is set and torch+transformers
                  are importable.
* ``heuristic`` - a transparent scorer over :class:`AcousticFeatures`. This is
                  the always-available fallback that powers the demo and the
                  pre-baked mock scenarios.

Both return a :class:`SpoofResult` with the same shape so the API never has to
care which one ran.
"""
from __future__ import annotations

from ..config import settings
from ..schemas import AcousticFeatures, SpoofResult, Speaker, Turn

# --- Heuristic reference ranges -------------------------------------------------
# Each tuple is (human_typical, suspicious_threshold, weight, "high"|"low").
# "high" means values ABOVE the threshold look synthetic; "low" the opposite.
_RULES: dict[str, tuple[float, str, str]] = {
    # Real speech jitters/shimmers more than TTS — *low* values are suspicious.
    "jitter": (0.010, "low", "prosodie trop régulière (jitter quasi nul)"),
    "shimmer": (0.040, "low", "amplitude anormalement lisse (shimmer faible)"),
    "f0_std": (15.0, "low", "intonation plate, peu de variation de pitch"),
    # Vocoders are buzzy/flat and unnaturally clean — *high* values suspicious.
    "spectral_flatness": (0.30, "high", "spectre vocodé (flatness élevée)"),
    "hnr": (25.0, "high", "voix trop propre (HNR irréaliste)"),
    "silence_ratio": (0.25, "high", "micro-silences de découpage/splicing"),
}
_WEIGHTS = {"jitter": 1.0, "shimmer": 1.0, "f0_std": 1.2,
            "spectral_flatness": 1.3, "hnr": 1.0, "silence_ratio": 0.8}


def _score_features(f: AcousticFeatures) -> tuple[float, list[str]]:
    score = 0.0
    total = 0.0
    reasons: list[str] = []
    for field, (thr, direction, why) in _RULES.items():
        val = getattr(f, field)
        w = _WEIGHTS[field]
        total += w
        if direction == "low":
            # how far below threshold, normalized
            hit = max(0.0, (thr - val) / thr) if thr else 0.0
        else:
            hit = max(0.0, (val - thr) / thr) if thr else 0.0
        hit = min(hit, 1.0)
        score += w * hit
        if hit > 0.45:
            reasons.append(why)
    return (score / total if total else 0.0), reasons


def _label(score: float) -> str:
    if score >= 0.55:
        return "synthetic"
    if score >= 0.3:
        return "uncertain"
    return "human"


class SpoofingDetector:
    """Lazy-loading detector that prefers the ML model, falls back to rules."""

    def __init__(self) -> None:
        self._model = None
        self._engine = "heuristic"
        self._tried_model = False

    def _maybe_load_model(self) -> None:
        if self._tried_model:
            return
        self._tried_model = True
        if not settings.spoofing_model_id:
            return
        try:  # pragma: no cover - optional heavy deps
            from transformers import pipeline  # type: ignore

            self._model = pipeline(
                "audio-classification", model=settings.spoofing_model_id
            )
            self._engine = "model"
        except Exception:
            self._model = None
            self._engine = "heuristic"

    @property
    def engine(self) -> str:
        self._maybe_load_model()
        return self._engine

    def score_caller(self, transcript: list[Turn]) -> SpoofResult:
        """Aggregate spoof score over all caller turns in the transcript."""
        caller_turns = [t for t in transcript if t.speaker == Speaker.CALLER]
        if not caller_turns:
            return SpoofResult(score=0.0, label="human", engine="heuristic",
                               reasons=["aucune parole de l'interlocuteur"])

        self._maybe_load_model()
        # NOTE: real audio path (engine == "model") would decode each turn's
        # waveform and run self._model. The mocked demo carries features, so we
        # always score on features here; the model branch is wired for when
        # real audio + checkpoint are present.
        scores: list[float] = []
        reasons: set[str] = set()
        for t in caller_turns:
            feats = t.features or AcousticFeatures()
            s, why = _score_features(feats)
            scores.append(s)
            reasons.update(why)

        # Weight the worst turn heavily — a single cloned segment is enough.
        agg = 0.6 * max(scores) + 0.4 * (sum(scores) / len(scores))
        return SpoofResult(
            score=round(agg, 3),
            label=_label(agg),
            engine="heuristic",  # feature path is always heuristic
            reasons=sorted(reasons)[:4],
        )


detector = SpoofingDetector()
