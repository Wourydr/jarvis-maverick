import json
import os
import datetime
from config import FICHIER_MEMOIRE, FICHIER_CONVERSATIONS

def charger_memoire():
    if not os.path.exists(FICHIER_MEMOIRE):
        return {
            "profil": {"nom": "", "ville": "Rufisque, Dakar", "langue": "français"},
            "preferences": [],
            "souvenirs": []
        }
    try:
        with open(FICHIER_MEMOIRE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "profil": {"nom": "", "ville": "Rufisque, Dakar", "langue": "français"},
            "preferences": [],
            "souvenirs": []
        }

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def se_souvenir(information: str = None, **kwargs):
    memoire = charger_memoire()
    elements = []
    if "nom" in kwargs:
        memoire["profil"]["nom"] = kwargs["nom"]
        elements.append(f"nom: {kwargs['nom']}")
    for k, v in kwargs.items():
        if k != "nom":
            memoire["souvenirs"].append(f"{k}: {v}")
            elements.append(f"{k}: {v}")
    if information:
        memoire["souvenirs"].append(str(information))
        elements.append(str(information))
    sauvegarder_memoire(memoire)
    return f"J'ai mémorisé : {', '.join(elements)}"

def lire_memoire():
    return charger_memoire()

# ========================================================
# GESTION PERMANENTE DE TOUTES LES CONVERSATIONS PASSÉES
# ========================================================

def charger_historique_permanent():
    """Charge l'intégralité des discussions enregistrées sur le disque."""
    if not os.path.exists(FICHIER_CONVERSATIONS):
        return []
    try:
        with open(FICHIER_CONVERSATIONS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def sauvegarder_message_permanent(role: str, content: str):
    """Enregistre chaque message échangé de façon permanente avec horodatage."""
    historique = charger_historique_permanent()
    maintenant = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    entree = {
        "date": maintenant,
        "role": role,
        "content": content
    }
    historique.append(entree)

    # Sauvegarde sécurisée
    try:
        with open(FICHIER_CONVERSATIONS, "w", encoding="utf-8") as f:
            json.dump(historique, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde historique : {e}")

def obtenir_contexte_conversations(nombre_messages: int = 12):
    """Récupère les derniers messages pour donner la mémoire continue à l'IA."""
    historique = charger_historique_permanent()
    if not historique:
        return []
    # On renvoie les derniers messages sous forme utilisable par Ollama
    recents = historique[-nombre_messages:]
    return [{"role": m["role"], "content": m["content"]} for m in recents]

def rechercher_dans_historique(requete: str):
    """Permet à Maverick de fouiller dans les anciennes discussions."""
    historique = charger_historique_permanent()
    requete_lower = requete.lower()
    correspondances = []
    for h in historique:
        if requete_lower in h.get("content", "").lower():
            correspondances.append(f"[{h.get('date')}] {h.get('role')} : {h.get('content')}")
    if not correspondances:
        return "Aucun souvenir trouvé sur ce sujet dans nos discussions passées."
    return "\n".join(correspondances[-8:])
