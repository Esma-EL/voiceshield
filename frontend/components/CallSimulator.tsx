"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type AnalyzeResponse,
  type HealthInfo,
  type ScenarioDetail,
  type ScenarioMeta,
} from "@/lib/api";
import { VoiceBadge } from "./VoiceBadge";
import { AnalysisPanel } from "./AnalysisPanel";

const TURN_MS = 1600; // pacing between turns during auto-play

export function CallSimulator() {
  const [scenarios, setScenarios] = useState<ScenarioMeta[]>([]);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ScenarioDetail | null>(null);
  const [shownTurns, setShownTurns] = useState(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Initial load.
  useEffect(() => {
    api.scenarios().then(setScenarios).catch((e) => setError(String(e)));
    api.health().then(setHealth).catch(() => {});
  }, []);

  // Auto-scroll the transcript as turns appear.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [shownTurns]);

  const stop = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    setPlaying(false);
  }, []);

  const selectScenario = useCallback(
    async (id: string) => {
      stop();
      setActiveId(id);
      setResult(null);
      setShownTurns(0);
      setError(null);
      try {
        setDetail(await api.scenario(id));
      } catch (e) {
        setError(String(e));
      }
    },
    [stop],
  );

  // Advance one turn: reveal it and re-analyze the call up to here.
  const advance = useCallback(
    async (id: string, nextCount: number) => {
      setShownTurns(nextCount);
      try {
        setResult(await api.analyzeScenario(id, nextCount));
      } catch (e) {
        setError(String(e));
      }
    },
    [],
  );

  // Auto-play loop.
  useEffect(() => {
    if (!playing || !detail || !activeId) return;
    if (shownTurns >= detail.transcript.length) {
      setPlaying(false);
      return;
    }
    timer.current = setTimeout(() => {
      advance(activeId, shownTurns + 1);
    }, shownTurns === 0 ? 200 : TURN_MS);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [playing, detail, activeId, shownTurns, advance]);

  const togglePlay = () => {
    if (!detail || !activeId) return;
    if (shownTurns >= detail.transcript.length) {
      // restart
      setShownTurns(0);
      setResult(null);
    }
    setPlaying((p) => !p);
  };

  const stepOnce = () => {
    if (!detail || !activeId || shownTurns >= detail.transcript.length) return;
    stop();
    advance(activeId, shownTurns + 1);
  };

  const badge = result?.badge ?? "verified";
  const finished = detail ? shownTurns >= detail.transcript.length : false;

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_minmax(360px,420px)]">
      {/* ---------------- Left: call panel ---------------- */}
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => selectScenario(s.id)}
              className={`rounded-xl border px-4 py-3 text-left transition-colors ${
                activeId === s.id
                  ? "border-shield bg-shield/10"
                  : "border-slate-800 bg-slate-900/40 hover:border-slate-600"
              }`}
            >
              <div className="text-sm font-semibold">{s.title}</div>
              <div className="text-xs text-slate-500">
                {s.channel} · {s.caller}
              </div>
            </button>
          ))}
        </div>

        {detail ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">{detail.channel}</div>
                <div className="font-semibold">{detail.caller}</div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={togglePlay}
                  className="rounded-lg bg-shield px-4 py-2 text-sm font-semibold text-white hover:bg-shield-dark"
                >
                  {playing ? "⏸ Pause" : finished ? "↻ Rejouer" : "▶ Simuler l'appel"}
                </button>
                <button
                  onClick={stepOnce}
                  disabled={finished}
                  className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:border-slate-500 disabled:opacity-40"
                >
                  Pas à pas
                </button>
              </div>
            </div>

            <div
              ref={scrollRef}
              className="max-h-[420px] space-y-3 overflow-y-auto pr-1"
            >
              {detail.transcript.slice(0, shownTurns).map((t, i) => (
                <div
                  key={i}
                  className={`flex animate-slideIn ${
                    t.speaker === "caller" ? "justify-start" : "justify-end"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                      t.speaker === "caller"
                        ? "rounded-tl-sm bg-slate-800 text-slate-100"
                        : "rounded-tr-sm bg-shield/20 text-sky-100"
                    }`}
                  >
                    <div className="mb-0.5 text-[10px] uppercase tracking-wide opacity-50">
                      {t.speaker === "caller" ? "Interlocuteur" : "Vous"}
                    </div>
                    {t.text}
                  </div>
                </div>
              ))}
              {shownTurns === 0 && (
                <div className="py-12 text-center text-sm text-slate-600">
                  Appuyez sur « Simuler l'appel » pour démarrer.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-800 p-10 text-center text-slate-500">
            Sélectionnez un scénario d'appel ci-dessus.
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
            <div className="mt-1 text-xs text-red-400/70">
              Le backend est-il démarré sur {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"} ?
            </div>
          </div>
        )}
      </div>

      {/* ---------------- Right: live verdict ---------------- */}
      <div className="space-y-4">
        <VoiceBadge state={badge} risk={result?.risk ?? 0} />
        {result && (
          <div
            className={`rounded-xl border p-4 text-sm ${
              badge === "fraud"
                ? "border-red-500/40 bg-red-500/10 text-red-200"
                : badge === "suspect"
                  ? "border-amber-500/40 bg-amber-500/10 text-amber-200"
                  : "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
            }`}
          >
            {result.headline}
          </div>
        )}
        <AnalysisPanel result={result} />
        {health && (
          <div className="text-center text-[11px] text-slate-600">
            moteurs · voix: {health.voice_engine} · contexte: {health.context_engine}
            {health.live_features ? " · audio live ✓" : ""}
          </div>
        )}
      </div>
    </div>
  );
}
