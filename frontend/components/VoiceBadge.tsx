"use client";

import type { BadgeState } from "@/lib/api";

const STYLES: Record<
  BadgeState,
  { ring: string; dot: string; label: string; sub: string }
> = {
  verified: {
    ring: "border-emerald-400/60 bg-emerald-500/10 text-emerald-300",
    dot: "bg-emerald-400",
    label: "Voice-Verified",
    sub: "Voix authentifiée",
  },
  suspect: {
    ring: "border-amber-400/60 bg-amber-500/10 text-amber-300",
    dot: "bg-amber-400",
    label: "Vigilance",
    sub: "Signaux ambigus",
  },
  fraud: {
    ring: "border-red-500/70 bg-red-500/10 text-red-300 animate-pulseRing",
    dot: "bg-red-500",
    label: "Fraude détectée",
    sub: "N'autorisez aucun paiement",
  },
};

export function VoiceBadge({
  state,
  risk,
}: {
  state: BadgeState;
  risk: number;
}) {
  const s = STYLES[state];
  return (
    <div
      className={`flex items-center gap-3 rounded-2xl border px-5 py-4 transition-colors duration-500 ${s.ring}`}
    >
      <span className="relative flex h-3.5 w-3.5">
        <span
          className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${s.dot} ${
            state !== "verified" ? "animate-ping" : ""
          }`}
        />
        <span className={`relative inline-flex h-3.5 w-3.5 rounded-full ${s.dot}`} />
      </span>
      <div className="leading-tight">
        <div className="text-base font-semibold">{s.label}</div>
        <div className="text-xs opacity-80">{s.sub}</div>
      </div>
      <div className="ml-auto text-right">
        <div className="text-2xl font-bold tabular-nums">
          {Math.round(risk * 100)}
        </div>
        <div className="text-[10px] uppercase tracking-wide opacity-70">
          score de risque
        </div>
      </div>
    </div>
  );
}
