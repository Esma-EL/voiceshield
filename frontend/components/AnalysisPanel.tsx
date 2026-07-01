"use client";

import type { AnalyzeResponse } from "@/lib/api";
import { CertificationStamp } from "./CertificationStamp";

function Meter({ value, danger }: { value: number; danger: boolean }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
      <div
        className={`h-full rounded-full transition-all duration-500 ${
          danger ? "bg-red-500" : value > 0.4 ? "bg-amber-400" : "bg-emerald-400"
        }`}
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

export function AnalysisPanel({ result }: { result: AnalyzeResponse | null }) {
  if (!result) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-500">
        Lancez la simulation d'appel pour voir l'analyse en temps réel.
      </div>
    );
  }

  const { voice, context, certification } = result;
  const voiceDanger = voice.label === "synthetic";

  return (
    <div className="space-y-5">
      {/* Voice analysis */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
        <header className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Analyse vocale</h3>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              voiceDanger
                ? "bg-red-500/15 text-red-300"
                : voice.label === "uncertain"
                  ? "bg-amber-500/15 text-amber-300"
                  : "bg-emerald-500/15 text-emerald-300"
            }`}
          >
            {voice.label === "synthetic"
              ? "voix synthétique"
              : voice.label === "uncertain"
                ? "incertain"
                : "voix humaine"}
          </span>
        </header>
        <Meter value={voice.score} danger={voiceDanger} />
        <div className="mt-1 text-xs text-slate-500">
          probabilité de deepfake : {Math.round(voice.score * 100)}% · moteur :{" "}
          {voice.engine}
        </div>
        {voice.reasons.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm text-slate-400">
            {voice.reasons.map((r) => (
              <li key={r} className="flex gap-2">
                <span className="text-slate-600">▹</span>
                {r}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Context analysis */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
        <header className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Analyse contextuelle</h3>
          <span className="text-xs text-slate-500">moteur : {context.engine}</span>
        </header>
        <Meter value={context.risk} danger={context.risk >= 0.65} />
        <p className="mt-2 text-sm text-slate-400">{context.summary}</p>
        {context.signals.length > 0 && (
          <ul className="mt-3 space-y-2">
            {context.signals
              .slice()
              .sort((a, b) => b.severity - a.severity)
              .map((s) => (
                <li
                  key={s.code}
                  className="animate-slideIn rounded-lg border border-slate-800 bg-slate-950/60 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-200">
                      {s.label}
                    </span>
                    <span
                      className={`text-xs font-semibold ${
                        s.severity >= 0.6 ? "text-red-300" : "text-amber-300"
                      }`}
                    >
                      {Math.round(s.severity * 100)}%
                    </span>
                  </div>
                  <p className="mt-1 text-xs italic text-slate-500">
                    {s.evidence}
                  </p>
                </li>
              ))}
          </ul>
        )}
      </section>

      <CertificationStamp cert={certification} />
    </div>
  );
}
