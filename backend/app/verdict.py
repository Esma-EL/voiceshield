"""Fuse the voice and context analyses into a single badge + certification."""
from __future__ import annotations

import hashlib

from .config import settings
from .schemas import (
    AnalyzeResponse,
    BadgeState,
    Certification,
    ContextResult,
    SpoofResult,
)


def _combined_risk(voice: SpoofResult, context: ContextResult) -> float:
    """Voice spoofing and context fraud reinforce each other (noisy-OR),
    with a bonus when BOTH fire — the signature of a real deepfake scam."""
    base = 1.0 - (1.0 - voice.score) * (1.0 - context.risk)
    if voice.score >= 0.5 and context.risk >= 0.4:
        base = min(1.0, base + 0.12)
    return round(base, 3)


def _badge(risk: float) -> BadgeState:
    if risk >= settings.risk_red:
        return "fraud"
    if risk >= settings.risk_amber:
        return "suspect"
    return "verified"


def _headline(badge: BadgeState, voice: SpoofResult, context: ContextResult) -> str:
    if badge == "verified":
        return "Voix authentifiée — aucune anomalie détectée."
    if badge == "suspect":
        bits = []
        if voice.label != "human":
            bits.append("voix possiblement synthétique")
        if context.signals:
            bits.append(context.signals[0].label.lower())
        return "Vigilance — " + (", ".join(bits) or "signaux ambigus") + "."
    # fraud
    bits = []
    if voice.label == "synthetic":
        bits.append("DEEPFAKE VOCAL")
    top = sorted(context.signals, key=lambda s: -s.severity)
    if top:
        bits.append(top[0].label.upper())
    return "FRAUDE PROBABLE — " + " + ".join(bits) + ". Ne validez aucun paiement."


def _certify(badge: BadgeState, scenario_id: str | None) -> Certification:
    if badge != "verified":
        return Certification(insured=False)
    seed = (scenario_id or "live").encode()
    policy = "ANT-" + hashlib.sha1(seed).hexdigest()[:8].upper()
    return Certification(
        insured=True, provider="Ant Insurance",
        policy_id=policy, coverage_eur=50_000,
    )


def build_verdict(
    voice: SpoofResult, context: ContextResult, scenario_id: str | None
) -> AnalyzeResponse:
    risk = _combined_risk(voice, context)
    badge = _badge(risk)
    return AnalyzeResponse(
        badge=badge,
        risk=risk,
        voice=voice,
        context=context,
        certification=_certify(badge, scenario_id),
        headline=_headline(badge, voice, context),
    )
