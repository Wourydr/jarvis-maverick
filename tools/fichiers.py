import os
from config import DOSSIER_DOCUMENTS

def chemin_securise(chemin):
    chemin_abs = os.path.abspath(os.path.join(DOSSIER_DOCUMENTS, chemin))
    return chemin_abs if chemin_abs.startswith(os.path.abspath(DOSSIER_DOCUMENTS)) else None

def lister_fichiers(dossier: str = "."):
    chemin = chemin_securise(dossier)
    if not chemin or not os.path.exists(chemin):
        return "Dossier introuvable ou non autorisé."
    return os.listdir(chemin)

def lire_fichier(chemin: str):
    chemin = chemin_securise(chemin)
    if not chemin or not os.path.isfile(chemin):
        return "Fichier introuvable ou non autorisé."
    with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()[:8000]

def creer_fichier(chemin: str, contenu: str):
    chemin = chemin_securise(chemin)
    if not chemin:
        return "Chemin non autorisé."
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    return f"Fichier créé : {chemin}"
