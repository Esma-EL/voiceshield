"""VoiceShield B2B — FastAPI backend.

Endpoints:
  GET  /api/health                 - liveness + which engines are active
  GET  /api/scenarios              - list demo scenarios (metadata)
  GET  /api/scenarios/{id}         - full scripted transcript for playback
  POST /api/analyze                - analyze a transcript -> badge + verdict
  POST /api/analyze/scenario/{id}  - analyze first N turns of a scenario
  POST /api/analyze/audio          - analyze an uploaded wav (live features)
"""
from __future__ import annotations

import io

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .analysis.llm import analyze_context
from .config import settings
from .detection import features as feat
from .detection.spoofing import detector
from .mock_data import get_scenario, list_scenarios
from .schemas import (
    AcousticFeatures,
    AnalyzeRequest,
    AnalyzeResponse,
    Speaker,
    Turn,
)
from .verdict import build_verdict

app = FastAPI(title="VoiceShield B2B", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _analyze(transcript: list[Turn], scenario_id: str | None) -> AnalyzeResponse:
    voice = detector.score_caller(transcript)
    context = analyze_context(transcript)
    return build_verdict(voice, context, scenario_id)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "voice_engine": detector.engine,
        "context_engine": "llm" if settings.dashscope_api_key else "rules",
        "live_features": feat.librosa_available(),
    }


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    return list_scenarios()


@app.get("/api/scenarios/{scenario_id}")
def scenario_detail(scenario_id: str) -> dict:
    s = get_scenario(scenario_id)
    if not s:
        raise HTTPException(404, "scénario inconnu")
    # Expose the transcript for playback but strip ground-truth flags.
    turns = [
        {"speaker": t.speaker.value, "text": t.text}
        for t in s["transcript"]
    ]
    return {
        "id": s["id"], "title": s["title"], "channel": s["channel"],
        "caller": s["caller"], "description": s["description"], "transcript": turns,
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    if not req.transcript:
        raise HTTPException(400, "transcript vide")
    return _analyze(req.transcript, req.scenario_id)


@app.post("/api/analyze/scenario/{scenario_id}", response_model=AnalyzeResponse)
def analyze_scenario(scenario_id: str, up_to_turn: int | None = None) -> AnalyzeResponse:
    """Analyze a scripted scenario. `up_to_turn` (1-based, exclusive upper
    bound) lets the frontend replay the call turn-by-turn and watch the badge
    flip live; omit it to analyze the whole call."""
    s = get_scenario(scenario_id)
    if not s:
        raise HTTPException(404, "scénario inconnu")
    transcript: list[Turn] = s["transcript"]
    if up_to_turn is not None:
        transcript = transcript[:max(0, up_to_turn)]
    if not transcript:
        # No turns yet -> trivially verified.
        transcript = [Turn(speaker=Speaker.AGENT, text="")]
    return _analyze(transcript, scenario_id)


@app.post("/api/analyze/audio", response_model=AnalyzeResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    text: str = Form(""),
) -> AnalyzeResponse:
    """Analyze a single uploaded caller turn from real audio.

    Requires librosa+soundfile (optional deps). Without them, returns 503 so the
    UI can fall back to the scripted scenarios.
    """
    if not feat.librosa_available():
        raise HTTPException(
            503, "extraction audio indisponible (installez librosa+soundfile)"
        )
    try:
        import soundfile as sf  # type: ignore
        import numpy as np

        raw = await file.read()
        samples, sr = sf.read(io.BytesIO(raw))
        samples = np.asarray(samples, dtype="float32")
        acoustic: AcousticFeatures = feat.extract_features(samples, sr)
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(400, f"audio illisible: {e}")

    turn = Turn(speaker=Speaker.CALLER, text=text, features=acoustic)
    return _analyze([turn], scenario_id=None)
