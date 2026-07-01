"""Context-fraud analysis over the call transcript.

Detects social-engineering patterns typical of CEO-fraud / faux-fournisseur
scams targeting PMEs: artificial urgency, bank-detail changes, authority
impersonation, secrecy pressure, abnormal amounts.

Engine selection:
* ``llm``   - Qwen via DashScope (set DASHSCOPE_API_KEY + install dashscope).
* ``rules`` - transparent French keyword/pattern engine (always available).

Both return a :class:`ContextResult` with identical shape.
"""
from __future__ import annotations

import json
import re

from ..config import settings
from ..schemas import ContextResult, FraudSignal, Speaker, Turn

# --- Rule engine ---------------------------------------------------------------
# Each rule: code, label, severity, regex patterns (lowercase, accents kept).
_PATTERNS: list[tuple[str, str, float, list[str]]] = [
    ("URGENCY", "Urgence anormale", 0.55, [
        r"\burgent", r"imm[ée]diat", r"tout de suite", r"avant la fermeture",
        r"d[èe]s maintenant", r"sans attendre", r"d[ée]lai", r"derni[èe]re minute",
        r"ne peut pas attendre",
    ]),
    ("BANK_CHANGE", "Changement de coordonnées bancaires", 0.85, [
        r"\brib\b", r"\biban\b", r"nouveau compte", r"changement de compte",
        r"nouvelles? coordonn[ée]es? bancaires?", r"nouvelle banque",
        r"virer sur", r"mettre [àa] jour le compte",
    ]),
    ("AUTHORITY", "Usurpation d'autorité", 0.45, [
        r"\bpdg\b", r"directeur g[ée]n[ée]ral", r"\bdaf\b", r"le patron",
        r"la direction", r"je suis le", r"de la part du", r"avocat", r"huissier",
    ]),
    ("SECRECY", "Pression au secret / confidentialité", 0.65, [
        r"confidentiel", r"ne (?:le )?dites? [àa] personne", r"entre nous",
        r"discr[èe]t", r"ne pr[ée]venez personne", r"sans en parler",
    ]),
    ("PAYMENT_PRESSURE", "Pression au paiement", 0.6, [
        r"virement", r"payer", r"r[ée]gler la facture", r"transf[ée]rer",
        r"d[ée]bloquer les fonds", r"acompte",
    ]),
    ("CHANNEL_SWITCH", "Demande de changer de canal", 0.4, [
        r"rappelez-moi sur", r"sur whatsapp", r"autre num[ée]ro",
        r"par sms", r"ne passez pas par",
    ]),
]

_AMOUNT_RE = re.compile(r"(\d[\d\s.,]{3,})\s*(?:€|euros?|k€|keur)", re.IGNORECASE)


def _caller_text(transcript: list[Turn]) -> str:
    return "\n".join(t.text for t in transcript if t.speaker == Speaker.CALLER)


def _rule_engine(transcript: list[Turn]) -> ContextResult:
    text = _caller_text(transcript)
    low = text.lower()
    signals: list[FraudSignal] = []

    for code, label, severity, patterns in _PATTERNS:
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                snippet = _snippet(text, m.start())
                signals.append(FraudSignal(
                    code=code, label=label, severity=severity, evidence=snippet,
                ))
                break  # one hit per category is enough

    amounts = _AMOUNT_RE.findall(text)
    if amounts:
        signals.append(FraudSignal(
            code="HIGH_AMOUNT", label="Montant élevé mentionné", severity=0.35,
            evidence=f"montant(s): {', '.join(a.strip() for a in amounts[:3])}",
        ))

    risk = _combine(signals)
    summary = _summarize(signals, risk)
    return ContextResult(risk=round(risk, 3), engine="rules",
                         signals=signals, summary=summary)


def _snippet(text: str, idx: int, width: int = 60) -> str:
    start = max(0, idx - width // 3)
    end = min(len(text), idx + width)
    s = text[start:end].replace("\n", " ").strip()
    return f"…{s}…"


def _combine(signals: list[FraudSignal]) -> float:
    """Noisy-OR over signal severities; combos compound but stay in [0,1]."""
    prod = 1.0
    for s in signals:
        prod *= (1.0 - s.severity)
    risk = 1.0 - prod
    # The deadliest combo: deepfake-friendly BANK_CHANGE + URGENCY.
    codes = {s.code for s in signals}
    if {"BANK_CHANGE", "URGENCY"} <= codes:
        risk = min(1.0, risk + 0.1)
    return risk


def _summarize(signals: list[FraudSignal], risk: float) -> str:
    if not signals:
        return "Aucun motif de fraude détecté dans la conversation."
    labels = ", ".join(sorted({s.label for s in signals}))
    level = "élevé" if risk >= 0.65 else "modéré" if risk >= 0.4 else "faible"
    return f"Risque contextuel {level}. Motifs: {labels}."


# --- LLM engine (Qwen / DashScope) --------------------------------------------
_SYSTEM = (
    "Tu es un analyste anti-fraude pour PME. On te donne la transcription d'un "
    "appel. Identifie les signaux d'ingénierie sociale (urgence artificielle, "
    "changement de coordonnées bancaires, usurpation d'autorité, pression au "
    "secret, pression au paiement, changement de canal). Réponds UNIQUEMENT en "
    "JSON: {\"risk\": float 0..1, \"summary\": str, \"signals\": "
    "[{\"code\": str, \"label\": str, \"severity\": float 0..1, "
    "\"evidence\": str}]}."
)


def _llm_engine(transcript: list[Turn]) -> ContextResult | None:
    if not settings.dashscope_api_key:
        return None
    try:  # pragma: no cover - optional + network
        import dashscope  # type: ignore
        from dashscope import Generation  # type: ignore

        dashscope.api_key = settings.dashscope_api_key
        convo = "\n".join(
            f"[{t.speaker.value}] {t.text}" for t in transcript
        )
        resp = Generation.call(
            model=settings.qwen_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": convo},
            ],
            result_format="message",
        )
        content = resp.output.choices[0].message.content  # type: ignore
        data = json.loads(_extract_json(content))
        signals = [FraudSignal(**s) for s in data.get("signals", [])]
        return ContextResult(
            risk=float(max(0.0, min(1.0, data.get("risk", _combine(signals))))),
            engine="llm",
            signals=signals,
            summary=data.get("summary", ""),
        )
    except Exception:
        return None  # any failure -> caller falls back to rules


def _extract_json(s: str) -> str:
    start = s.find("{")
    end = s.rfind("}")
    return s[start:end + 1] if start != -1 and end != -1 else "{}"


def analyze_context(transcript: list[Turn]) -> ContextResult:
    """Public entry point: try the LLM, fall back to the rule engine."""
    return _llm_engine(transcript) or _rule_engine(transcript)
