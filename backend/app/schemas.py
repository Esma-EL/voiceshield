"""Pydantic models shared across the API."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Speaker(str, Enum):
    CALLER = "caller"   # the (potentially fraudulent) interlocutor
    AGENT = "agent"     # the PME employee using VoiceShield


class AcousticFeatures(BaseModel):
    """Compact acoustic fingerprint of a voice turn.

    In the real pipeline these come from librosa on the call audio. In the
    mocked scenarios they are pre-baked so the demo is deterministic.
    Values are roughly normalized; the heuristic detector knows their scales.
    """
    jitter: float = Field(0.0, description="Cycle-to-cycle pitch perturbation; TTS tends to be unnaturally low.")
    shimmer: float = Field(0.0, description="Amplitude perturbation; synthetic voices are too smooth.")
    spectral_flatness: float = Field(0.0, description="0=tonal, 1=noise-like; vocoders skew flat/buzzy.")
    hnr: float = Field(20.0, description="Harmonics-to-noise ratio (dB); synthesis is often too clean.")
    f0_std: float = Field(0.0, description="Std-dev of fundamental frequency; flat prosody is a tell.")
    silence_ratio: float = Field(0.0, description="Fraction of unnatural micro-silences / splicing.")


class Turn(BaseModel):
    speaker: Speaker
    text: str
    features: AcousticFeatures | None = None
    # Ground-truth flag, only present in mock scenarios (never trusted by detector).
    is_synthetic: bool | None = None


class AnalyzeRequest(BaseModel):
    transcript: list[Turn]
    scenario_id: str | None = None


class SpoofResult(BaseModel):
    score: float = Field(..., ge=0, le=1, description="P(synthetic voice) over caller turns.")
    label: Literal["human", "uncertain", "synthetic"]
    engine: Literal["model", "heuristic"]
    reasons: list[str] = []


class FraudSignal(BaseModel):
    code: str
    label: str
    severity: float = Field(..., ge=0, le=1)
    evidence: str


class ContextResult(BaseModel):
    risk: float = Field(..., ge=0, le=1, description="Aggregate context-fraud risk.")
    engine: Literal["llm", "rules"]
    signals: list[FraudSignal] = []
    summary: str = ""


class Certification(BaseModel):
    """Mock 'assuré par Ant Insurance' stamp, only emitted when verified."""
    insured: bool
    provider: str = "Ant Insurance"
    policy_id: str | None = None
    coverage_eur: int | None = None


BadgeState = Literal["verified", "suspect", "fraud"]


class AnalyzeResponse(BaseModel):
    badge: BadgeState
    risk: float = Field(..., ge=0, le=1, description="Combined risk driving the badge.")
    voice: SpoofResult
    context: ContextResult
    certification: Certification
    headline: str
