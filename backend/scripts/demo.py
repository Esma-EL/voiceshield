"""Offline demo: run every mock scenario through the full pipeline and print
the live badge evolution, turn by turn. No server needed.

    python -m scripts.demo          (from the backend/ directory)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows consoles default to cp1252; force UTF-8 so emojis/accents render.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.analysis.llm import analyze_context           # noqa: E402
from app.detection.spoofing import detector            # noqa: E402
from app.mock_data import SCENARIOS                     # noqa: E402
from app.verdict import build_verdict                   # noqa: E402

BADGE_ICON = {"verified": "🟢", "suspect": "🟠", "fraud": "🔴"}


def run() -> None:
    for sid, s in SCENARIOS.items():
        print("\n" + "=" * 72)
        print(f"  {s['title']}  ({s['channel']})")
        print(f"  Interlocuteur : {s['caller']}")
        print("=" * 72)
        turns = s["transcript"]
        for i in range(1, len(turns) + 1):
            window = turns[:i]
            voice = detector.score_caller(window)
            ctx = analyze_context(window)
            verdict = build_verdict(voice, ctx, sid)
            last = turns[i - 1]
            speaker = "👤" if last.speaker.value == "caller" else "🛡️ "
            print(f"\n{speaker} {last.text}")
            print(f"   {BADGE_ICON[verdict.badge]} {verdict.badge.upper():9} "
                  f"risk={verdict.risk:.2f}  "
                  f"voix={voice.label}({voice.score:.2f})  "
                  f"contexte={ctx.risk:.2f}")
        print(f"\n  → VERDICT FINAL : {BADGE_ICON[verdict.badge]} {verdict.headline}")
        if verdict.certification.insured:
            print(f"  → Certifié : assuré par {verdict.certification.provider} "
                  f"(police {verdict.certification.policy_id}, "
                  f"couverture {verdict.certification.coverage_eur:,} €)")
    print()


if __name__ == "__main__":
    run()
