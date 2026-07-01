"use client";

import type { Certification } from "@/lib/api";

export function CertificationStamp({ cert }: { cert: Certification }) {
  if (!cert.insured) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-sm text-slate-400">
        <div className="font-medium text-slate-300">Non certifié</div>
        Cet échange ne peut pas être assuré tant qu'une anomalie est détectée.
      </div>
    );
  }
  return (
    <div className="relative overflow-hidden rounded-xl border border-emerald-500/40 bg-gradient-to-br from-emerald-500/10 to-sky-500/10 p-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">🛡️</span>
        <span className="font-semibold text-emerald-300">
          Assuré par {cert.provider}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-300">
        Transaction couverte jusqu'à{" "}
        <span className="font-semibold text-emerald-200">
          {cert.coverage_eur?.toLocaleString("fr-FR")} €
        </span>
        .
      </p>
      <p className="mt-2 font-mono text-xs text-slate-400">
        Police {cert.policy_id}
      </p>
      <span className="pointer-events-none absolute -right-6 -top-6 rotate-12 rounded-full border-2 border-emerald-400/30 px-8 py-8 text-[10px] font-bold uppercase tracking-widest text-emerald-400/30">
        certifié
      </span>
    </div>
  );
}
