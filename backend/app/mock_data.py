"""Pre-baked demo scenarios.

Each scenario is a scripted call played turn-by-turn by the frontend. Caller
turns carry pre-computed acoustic features so the heuristic detector produces a
deterministic, demo-friendly verdict without needing real audio. Drop in real
audio + a model later and these features get replaced by live extraction.
"""
from __future__ import annotations

from .schemas import AcousticFeatures, Speaker, Turn

# --- Reusable feature fingerprints --------------------------------------------
HUMAN = AcousticFeatures(
    jitter=0.021, shimmer=0.061, spectral_flatness=0.18,
    hnr=17.5, f0_std=28.0, silence_ratio=0.12,
)
SYNTHETIC = AcousticFeatures(
    jitter=0.002, shimmer=0.010, spectral_flatness=0.55,
    hnr=34.0, f0_std=4.0, silence_ratio=0.45,
)


def _c(text: str, synthetic: bool = False) -> Turn:
    return Turn(
        speaker=Speaker.CALLER,
        text=text,
        features=SYNTHETIC if synthetic else HUMAN,
        is_synthetic=synthetic,
    )


def _a(text: str) -> Turn:
    return Turn(speaker=Speaker.AGENT, text=text)


SCENARIOS: dict[str, dict] = {
    "legit-supplier": {
        "id": "legit-supplier",
        "title": "Appel fournisseur légitime",
        "channel": "WhatsApp Business",
        "caller": "Martin Dubois — Fournisseur Logipièces",
        "description": "Un fournisseur connu confirme une livraison. Voix humaine, aucun motif de fraude.",
        "transcript": [
            _a("Logipièces bonjour, que puis-je pour vous ?"),
            _c("Bonjour, c'est Martin de Logipièces. Je vous appelle pour confirmer la livraison de mardi."),
            _a("Parfait, on attend bien la palette de roulements."),
            _c("Exactement. Même adresse, même conditions de paiement à 30 jours. Rien ne change de notre côté."),
            _a("Très bien, merci Martin."),
            _c("Je vous envoie le bon de livraison par mail comme d'habitude. Bonne journée !"),
        ],
    },
    "ceo-deepfake": {
        "id": "ceo-deepfake",
        "title": "Fraude au président (deepfake)",
        "channel": "WhatsApp Business",
        "caller": "« PDG » — voix clonée",
        "description": "Voix clonée du PDG : urgence, secret et virement immédiat. Le combo qui doit virer au rouge.",
        "transcript": [
            _a("Allô ?"),
            _c("C'est le PDG. J'ai besoin de vous immédiatement, c'est urgent et confidentiel.", synthetic=True),
            _a("Bien sûr, je vous écoute."),
            _c("On finalise une acquisition. Vous devez faire un virement de 48 000 € tout de suite, "
               "avant la fermeture de la banque.", synthetic=True),
            _a("C'est inhabituel... vers quel compte ?"),
            _c("Je vous envoie de nouvelles coordonnées bancaires, un nouvel IBAN. "
               "Ne dites à personne, c'est entre nous, l'opération est secrète.", synthetic=True),
            _a("D'accord..."),
            _c("Rappelez-moi sur WhatsApp si besoin, mais faites le virement maintenant.", synthetic=True),
        ],
    },
    "bank-change-human": {
        "id": "bank-change-human",
        "title": "Faux fournisseur (voix humaine)",
        "channel": "AliTelecom",
        "caller": "« Comptabilité fournisseur »",
        "description": "Voix humaine mais arnaque au changement de RIB. La voix passe, le contexte doit alerter.",
        "transcript": [
            _a("Service comptabilité, bonjour."),
            _c("Bonjour, je suis du service comptabilité de votre fournisseur. "
               "Nos coordonnées bancaires ont changé."),
            _a("Ah ? Vous avez changé de banque ?"),
            _c("Oui, merci de mettre à jour le compte. Je vous communique le nouveau RIB pour la prochaine facture."),
            _a("Il faut que je vérifie avec mon responsable."),
            _c("C'est assez urgent, la facture est à régler avant vendredi. "
               "Pouvez-vous virer sur le nouvel IBAN dès aujourd'hui ?"),
        ],
    },
}


def list_scenarios() -> list[dict]:
    """Public scenario metadata (without leaking ground-truth flags)."""
    out = []
    for s in SCENARIOS.values():
        out.append({
            "id": s["id"],
            "title": s["title"],
            "channel": s["channel"],
            "caller": s["caller"],
            "description": s["description"],
            "turns": len(s["transcript"]),
        })
    return out


def get_scenario(scenario_id: str) -> dict | None:
    return SCENARIOS.get(scenario_id)
