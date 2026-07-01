# 🛡️ VoiceShield B2B

> Copilote anti-fraude vocale pour PME — détecte en temps réel les **deepfakes
> vocaux** ET les **patterns de fraude** (urgence anormale, changement de RIB,
> usurpation d'autorité) sur les appels WhatsApp Business / AliTelecom.

Badge **« Voice-Verified »** vert qui passe au **rouge** dès qu'une anomalie est
détectée, avec certification mockée **« Assuré par Ant Insurance »** quand
l'échange est sain.

MVP hackathon « Build from 0 ». Tout fonctionne sans clé API ni modèle lourd
grâce à des moteurs de repli ; le code est structuré pour brancher de vrais
modèles ensuite.

---

## Architecture

```
voiceshield-b2b/
├── backend/                    FastAPI (Python 3.11)
│   ├── app/
│   │   ├── main.py             API REST (+ CORS)
│   │   ├── schemas.py          modèles Pydantic partagés
│   │   ├── config.py           config / sélection des moteurs
│   │   ├── verdict.py          fusion voix + contexte → badge + certification
│   │   ├── mock_data.py        3 scénarios d'appel scriptés
│   │   ├── detection/
│   │   │   ├── spoofing.py     anti-spoofing (modèle HF/ModelScope OU heuristique)
│   │   │   └── features.py     extraction de features acoustiques (librosa)
│   │   └── analysis/
│   │       └── llm.py          analyse contexte (Qwen/DashScope OU règles FR)
│   ├── scripts/
│   │   ├── demo.py             démo CLI : rejoue tous les scénarios
│   │   └── gen_demo_audio.py   génère human.wav / synthetic.wav
│   └── demo_audio/             audio d'exemple
└── frontend/                   Next.js 14 + React + Tailwind (TypeScript strict)
    ├── app/                    page + layout
    ├── components/             simulateur d'appel, badge live, panneau d'analyse
    └── lib/api.ts              client typé de l'API
```

### Comment le verdict est calculé

1. **Voix** — `detection/spoofing.py` score la probabilité de voix synthétique.
   Avec `SPOOFING_MODEL_ID` + `torch`/`transformers` installés → vrai modèle.
   Sinon → heuristique transparente sur jitter, shimmer, flatness spectrale,
   HNR, variation de pitch, micro-silences.
2. **Contexte** — `analysis/llm.py` analyse la transcription. Avec
   `DASHSCOPE_API_KEY` + SDK `dashscope` → Qwen. Sinon → moteur de règles FR
   (urgence, changement bancaire, autorité, secret, pression au paiement…).
3. **Fusion** — `verdict.py` combine les deux risques (noisy-OR, bonus si les
   deux signaux se renforcent) → badge `verified` / `suspect` / `fraud`, et
   émet la certification Ant Insurance uniquement si `verified`.

Les deux détecteurs dégradent proprement : **l'appli tourne entièrement sur les
replis**, donc la démo marche toujours.

---

## Lancer la démo

Prérequis : **Python 3.11+** et **Node 20+**.

### 1. Backend (FastAPI)

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate           # Windows ; macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000  (docs : /docs)
```

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
copy .env.local.example .env.local    # macOS/Linux : cp
npm run dev                            # http://localhost:3000
```

Ouvrez **http://localhost:3000**, choisissez un scénario et cliquez
**« Simuler l'appel »** : la conversation se déroule tour par tour et le badge
réagit en direct.

### 3. Démo en ligne de commande (sans navigateur)

Rejoue les 3 scénarios et affiche l'évolution du badge tour par tour :

```bash
cd backend
python -m scripts.demo
```

### 4. Audio d'exemple

```bash
cd backend
python scripts/gen_demo_audio.py     # crée demo_audio/human.wav et synthetic.wav
```

Pour tester l'analyse sur de l'audio réel, installez les deps optionnelles
(`librosa`, `soundfile` dans `requirements.txt`) puis :

```bash
curl -X POST http://localhost:8000/api/analyze/audio \
  -F "file=@demo_audio/synthetic.wav" -F "text=virement urgent nouvel IBAN"
```

### 5. Tests end-to-end (Playwright)

Vérifie le comportement du badge live dans un vrai navigateur (le deepfake fait
passer le badge au rouge ; l'appel légitime reste vert + assuré). Playwright
démarre automatiquement le backend et le frontend.

Prérequis (une fois) : le venv backend créé + `pip install -r requirements.txt`,
puis depuis `frontend/` :

```bash
npm install
npx playwright install chromium   # navigateur de test (une fois)
npm run test:e2e
```

---

## Scénarios inclus

| Scénario | Canal | Voix | Contexte | Verdict attendu |
|---|---|---|---|---|
| Appel fournisseur légitime | WhatsApp Business | humaine | sain | 🟢 Vérifié + assuré |
| Fraude au président (deepfake) | WhatsApp Business | **synthétique** | urgence + RIB + secret | 🔴 Fraude |
| Faux fournisseur | AliTelecom | humaine | changement de RIB | 🔴 Fraude (contexte seul) |

Le 3ᵉ scénario illustre la valeur du double moteur : la **voix passe**, mais le
**contexte** déclenche l'alerte.

---

## Brancher de vrais modèles

| Brique | Repli (défaut) | Réel |
|---|---|---|
| Anti-spoofing | heuristique features | `SPOOFING_MODEL_ID` + `torch`/`transformers` |
| Analyse contexte | règles FR | `DASHSCOPE_API_KEY` + `dashscope` (Qwen) |
| Features audio | features pré-calculées | `librosa` + `soundfile` |

Voir `backend/.env.example`. Aucune logique d'API à changer : les moteurs réels
renvoient exactement le même schéma que les replis.

> ⚠️ Démo hackathon : données simulées, certification « Ant Insurance » mockée.
