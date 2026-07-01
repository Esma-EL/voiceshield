# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

VoiceShield B2B — an anti-fraud copilot for SMEs ("PME"). It detects, in real
time, whether a caller's voice (WhatsApp Business / AliTelecom) is a **deepfake**
AND flags **social-engineering fraud patterns** in the conversation (abnormal
urgency, bank-detail changes, authority impersonation). The UI shows a live
"Voice-Verified" badge that flips green → amber → red, plus a mocked
"Assuré par Ant Insurance" certification when the exchange is clean.

Hackathon MVP. Everything is mocked/heuristic where real-time real models aren't
realistic, but the code is structured so real models drop in without touching the
API surface.

## Commands

Backend (from `backend/`, with the venv activated — `.venv\Scripts\activate`):
- `uvicorn app.main:app --reload` — run API on http://localhost:8000 (docs at `/docs`)
- `python -m scripts.demo` — replay all scenarios in the terminal, turn by turn
  (the fastest way to sanity-check detection logic; no server needed)
- `python scripts/gen_demo_audio.py` — regenerate `demo_audio/{human,synthetic}.wav`
- `pip install -r requirements.txt` — core deps; optional ML/LLM deps are
  commented at the bottom of that file

Frontend (from `frontend/`):
- `npm run dev` — Next.js dev server on http://localhost:3000
- `npm run typecheck` — `tsc --noEmit` (TypeScript is **strict**, plus
  `noUnusedLocals`/`noUnusedParameters` — keep this green)
- `npm run build` — production build (also runs lint + type checks)
- `npm run lint` — Next/ESLint

There is no automated test suite yet; `scripts/demo.py` is the de-facto
end-to-end check for the detection pipeline.

## Architecture — the big picture

The whole system is a two-engine detector fused into one verdict. Read these
together to understand a change:

1. **Voice anti-spoofing** (`backend/app/detection/spoofing.py`) →
   `SpoofResult`. Two interchangeable engines selected at runtime: a real
   HF/ModelScope model (`model`) or a transparent acoustic-feature heuristic
   (`heuristic`). Features come from `detection/features.py` (librosa) on real
   audio, or are pre-baked on mock turns.
2. **Context analysis** (`backend/app/analysis/llm.py`) → `ContextResult`. Either
   Qwen via DashScope (`llm`) or a French regex/keyword rule engine (`rules`).
3. **Fusion** (`backend/app/verdict.py`) → `AnalyzeResponse`. Combines the two
   risks (noisy-OR + a bonus when both fire — the deepfake-scam signature), maps
   to the `verified`/`suspect`/`fraud` badge, and emits the Ant Insurance
   certification only when `verified`.

**Key invariant: each engine and its fallback return the *same* Pydantic schema**
(`schemas.py`). `main.py` and the frontend never branch on which engine ran.
When adding a real model, conform to the existing `SpoofResult`/`ContextResult`
shape rather than changing callers.

**Graceful degradation is a hard requirement.** With no API keys and no optional
deps installed, the app must still run fully on the fallbacks (the demo depends
on this). Optional imports (`torch`, `transformers`, `librosa`, `dashscope`) are
always wrapped in try/except and selected via `config.py`; never make them
hard imports.

### Frontend flow

`components/CallSimulator.tsx` is the orchestrator (client component). It loads a
scenario, reveals turns one at a time, and after each turn POSTs to
`/api/analyze/scenario/{id}?up_to_turn=N` — the backend is **stateless** and
re-scores the transcript prefix each time, which is what makes the badge update
live. `lib/api.ts` holds the typed client and mirrors the backend schemas
exactly; keep the two in sync when changing any response model.

### Mock scenarios

`backend/app/mock_data.py` defines the three scripted calls. Caller turns carry
pre-computed `AcousticFeatures` (the `HUMAN` / `SYNTHETIC` fingerprints) so the
heuristic detector is deterministic. The detector's thresholds in
`spoofing.py` (`_RULES`) and these fingerprints are **calibrated together** — if
you change one, re-run `python -m scripts.demo` and confirm the deepfake scenario
still reads `synthetic` (score ≥ 0.55) and the legit one stays `human`.

## Conventions

- Backend: Python type hints throughout; Pydantic for all I/O models.
- Frontend: TypeScript strict; Tailwind for styling (config in
  `tailwind.config.ts`, custom `shield` color + badge animations there).
- User-facing copy and fraud-pattern labels are in **French** (the target
  market is French SMEs) — keep new UI/strings/rules in French.
- Windows note: terminal scripts force UTF-8 stdout (cp1252 default breaks
  emoji/accents) — see the top of `scripts/demo.py`.
