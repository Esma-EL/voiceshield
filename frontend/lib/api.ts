// Typed client for the VoiceShield FastAPI backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type BadgeState = "verified" | "suspect" | "fraud";
export type Speaker = "caller" | "agent";

export interface ScenarioMeta {
  id: string;
  title: string;
  channel: string;
  caller: string;
  description: string;
  turns: number;
}

export interface TranscriptTurn {
  speaker: Speaker;
  text: string;
}

export interface ScenarioDetail extends Omit<ScenarioMeta, "turns"> {
  transcript: TranscriptTurn[];
}

export interface SpoofResult {
  score: number;
  label: "human" | "uncertain" | "synthetic";
  engine: "model" | "heuristic";
  reasons: string[];
}

export interface FraudSignal {
  code: string;
  label: string;
  severity: number;
  evidence: string;
}

export interface ContextResult {
  risk: number;
  engine: "llm" | "rules";
  signals: FraudSignal[];
  summary: string;
}

export interface Certification {
  insured: boolean;
  provider: string;
  policy_id: string | null;
  coverage_eur: number | null;
}

export interface AnalyzeResponse {
  badge: BadgeState;
  risk: number;
  voice: SpoofResult;
  context: ContextResult;
  certification: Certification;
  headline: string;
}

export interface HealthInfo {
  status: string;
  voice_engine: "model" | "heuristic";
  context_engine: "llm" | "rules";
  live_features: boolean;
}

async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} — ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => getJSON<HealthInfo>("/api/health"),
  scenarios: () => getJSON<ScenarioMeta[]>("/api/scenarios"),
  scenario: (id: string) => getJSON<ScenarioDetail>(`/api/scenarios/${id}`),
  analyzeScenario: (id: string, upToTurn: number) =>
    getJSON<AnalyzeResponse>(
      `/api/analyze/scenario/${id}?up_to_turn=${upToTurn}`,
      { method: "POST" },
    ),
};
