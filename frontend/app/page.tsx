import { CallSimulator } from "@/components/CallSimulator";

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-10">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🛡️</span>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              VoiceShield <span className="text-shield">B2B</span>
            </h1>
            <p className="text-sm text-slate-400">
              Copilote anti-fraude vocale pour PME — détection deepfake +
              analyse contextuelle en temps réel.
            </p>
          </div>
        </div>
      </header>

      <CallSimulator />

      <footer className="mt-12 border-t border-slate-900 pt-6 text-center text-xs text-slate-600">
        Démo hackathon — données simulées. Détection vocale et analyse LLM
        branchables sur de vrais modèles (HuggingFace / Qwen). Certification
        « Ant Insurance » mockée.
      </footer>
    </main>
  );
}
