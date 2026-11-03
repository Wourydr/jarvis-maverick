import json
import re
import datetime
import threading
import ollama
from config import MODELE_OLLAMA
from tools.memoire import (
    se_souvenir, lire_memoire,
    charger_historique_permanent, sauvegarder_message_permanent,
    obtenir_contexte_conversations, rechercher_dans_historique
)
from tools.fichiers import lister_fichiers, lire_fichier, creer_fichier
from tools.web import recherche_web, lire_page
from tools.notion import rechercher_notion, lire_page_notion
from tools.gmail_tools import lire_derniers_mails, envoyer_mail
from tools.voix import parler, ecouter_microphone, detecter_langue_texte

OUTILS = {
    "lister_fichiers": {
        "description": "Liste les fichiers présents dans le dossier documents.",
        "fonction": lister_fichiers,
        "arguments": {"dossier": "chemin relatif, '.' par défaut"}
    },
    "lire_fichier": {
        "description": "Lit le contenu d'un fichier dans le dossier documents.",
        "fonction": lire_fichier,
        "arguments": {"chemin": "nom du fichier"}
    },
    "creer_fichier": {
        "description": "Crée ou écrit un fichier dans le dossier documents.",
        "fonction": creer_fichier,
        "arguments": {"chemin": "nom du fichier", "contenu": "texte à écrire"},
        "dangerous": True
    },
    "se_souvenir": {
        "description": "Mémorise une information importante dans la mémoire long terme.",
        "fonction": se_souvenir,
        "arguments": {"information": "l'information à enregistrer"}
    },
    "lire_memoire": {
        "description": "Consulte le profil et les faits mémorisés sur l'utilisateur.",
        "fonction": lire_memoire,
        "arguments": {}
    },
    "rechercher_dans_historique": {
        "description": "Fouille dans l'historique complet de toutes nos discussions passées pour retrouver un sujet précis.",
        "fonction": rechercher_dans_historique,
        "arguments": {"requete": "mot-clé ou sujet recherché"}
    },
    "recherche_web": {
        "description": "Cherche des faits réels ou les actualités en direct sur Internet via DuckDuckGo.",
        "fonction": recherche_web,
        "arguments": {"requete": "sujet précis de recherche"}
    },
    "lire_page": {
        "description": "Lit le contenu textuel d'une page web via son lien.",
        "fonction": lire_page,
        "arguments": {"url": "adresse URL complète"}
    },
    "rechercher_notion": {
        "description": "Recherche des pages dans Notion.",
        "fonction": rechercher_notion,
        "arguments": {"requete": "texte à chercher"}
    },
    "lire_page_notion": {
        "description": "Lit une page Notion via son ID.",
        "fonction": lire_page_notion,
        "arguments": {"page_id": "identifiant de page"}
    },
    "lire_derniers_mails": {
        "description": "Lit les derniers emails de la boîte Gmail.",
        "fonction": lire_derniers_mails,
        "arguments": {"nombre": "nombre d'emails"}
    },
    "envoyer_mail": {
        "description": "Envoie un email via Gmail.",
        "fonction": envoyer_mail,
        "arguments": {"destinataire": "email", "sujet": "sujet", "corps": "message"},
        "dangerous": True
    }
}

PROMPT_ANALYSEUR = """Tu es le routeur d'outils de MAVERICK.
Analyse la demande de l'utilisateur et détermine si un outil doit être appelé.

Outils disponibles :
- lister_fichiers(dossier=".")
- lire_fichier(chemin="nom")
- creer_fichier(chemin="nom", contenu="texte")
- se_souvenir(information="...")
- lire_memoire()
- rechercher_dans_historique(requete="...")
- recherche_web(requete="...") : OBLIGATOIRE pour toute question sur l'actualité, les événements récents, la météo, le sport, les personnalités politiques.
- lire_page(url="https://...")
- rechercher_notion(requete="...")
- lire_page_notion(page_id="...")
- lire_derniers_mails(nombre=5)
- envoyer_mail(destinataire="...", sujet="...", corps="...")

RÈGLE :
Réponds UNIQUEMENT en JSON sous la forme :
{"action": "outil", "outil": "<nom_outil>", "arguments": {<arguments>}}
OU
{"action": "discuter"}
"""

def detecter_action_rapide(texte):
    """
    Routage déterministe ultra-rapide (< 1 ms).
    Évite 15 à 20 secondes de latence inutile en court-circuitant l'analyseur LLM.
    """
    t = texte.lower().strip()
    
    # 0. Commande de changement de langue vocal & texte
    if any(k in t for k in ["parle anglais", "parle en anglais", "speak english", "switch to english", "can you speak english", "in english please"]):
        return ("changer_langue", {"langue": "en"})

    if any(k in t for k in ["parle français", "parle francais", "parle en français", "speak french", "switch to french", "in french please"]):
        return ("changer_langue", {"langue": "fr"})

    # 0.1 Bascule de voix Iron Man / J.A.R.V.I.S.
    if any(k in t for k in ["voix de jarvis", "voie de jarvis", "voix d'iron man", "voie d'iron man", "voix d'aron man", "voie d'aron man", "voix iron man", "mets la voix de jarvis", "mets la voix d'iron man", "la voix d'iron man", "la voie d'aron man"]):
        return ("changer_profil_voix", {"profil": "jarvis"})

    if any(k in t for k in ["voix de tony stark", "voie de tony stark", "voix de tony", "voix de stark", "mets la voix de stark"]):
        return ("changer_profil_voix", {"profil": "stark"})

    # 0.2 Bascule vers Open WebUI
    if any(k in t for k in ["open webui", "openwebui", "studio webui", "ouvre webui", "lance webui", "affiche webui", "open web ui"]):
        return ("ouvrir_open_webui", {})
    m_nom = re.search(r'(?:je m\'appelle|mon pr[ée]nom est|mon nom est|mon surnom est)\s+([a-zA-Z0-9_\- ]+)', t)
    if m_nom:
        val = m_nom.group(1).strip().capitalize()
        return ("se_souvenir", {"information": f"Nom/Prénom : {val}"})

    if any(k in t for k in ["retiens que", "mémorise", "memorise", "souviens-toi de", "note que"]):
        info = re.sub(r'^(?:retiens que|m[ée]morise que|m[ée]morise|souviens-toi de|note que)\s*', '', texte, flags=re.I).strip()
        return ("se_souvenir", {"information": info})

    # 2. Historique de discussion passé
    if any(k in t for k in ["de quoi on a parlé", "de quoi on parlait", "notre dernière discussion", "nos anciennes discussions", "tu te souviens quand on"]):
        return ("rechercher_dans_historique", {"requete": texte})

    if any(k in t for k in ["que sais-tu sur moi", "qu'est-ce que tu sais sur moi", "lire mémoire", "lire memoire", "mes souvenirs"]):
        return ("lire_memoire", {})

    # 3. Fichiers
    if any(k in t for k in ["quels fichiers", "liste les fichiers", "lister fichiers", "fichiers as-tu", "fichiers disponibles"]):
        return ("lister_fichiers", {"dossier": "."})

    m_creer = re.search(r'(?:cr[ée]e|cr[ée]er)\s+(?:un\s+)?fichier\s+([a-zA-Z0-9_\-\.]+)(?:\s+avec\s+(?:le\s+texte|le\s+contenu)?\s*[:\s]\s*(.*))?', texte, flags=re.I)
    if m_creer:
        nom_f = m_creer.group(1).strip()
        contenu_f = m_creer.group(2) or ""
        return ("creer_fichier", {"chemin": nom_f, "contenu": contenu_f.strip()})

    m_lire = re.search(r'(?:lis|lire|affiche|afficher)\s+(?:le\s+)?fichier\s+([a-zA-Z0-9_\-\.]+)', texte, flags=re.I)
    if m_lire:
        return ("lire_fichier", {"chemin": m_lire.group(1).strip()})

    # 4. Gmail
    if any(k in t for k in ["derniers mails", "mes mails", "lire mails", "mes emails", "derniers emails"]):
        return ("lire_derniers_mails", {"nombre": 5})

    # 5. Notion
    if "notion" in t and any(k in t for k in ["cherche", "trouve", "recherche"]):
        req = re.sub(r'^(?:cherche|recherche|trouve)\s*', '', texte, flags=re.I).replace("dans notion", "").replace("sur notion", "").strip()
        return ("rechercher_notion", {"requete": req})

    # 6. Actualités et événements récents
    mots_cles_actualite = [
        "se passe", "se passer", "quoi de neuf", "les infos", "l'info",
        "les informations", "les nouvelles", "l'actualité", "l'actualite",
        "l'actu", "actualités", "actualites", "dans le monde", "en ce moment",
        "dernières nouvelles", "dernieres nouvelles", "aujourd'hui", "aujourd hui"
    ]
    if any(k in t for k in mots_cles_actualite):
        sujet = "actualités dans le monde"
        if "france" in t:
            sujet = "actualités en France"
        elif "sénégal" in t or "senegal" in t:
            sujet = "actualités au Sénégal"
        elif "politique" in t:
            sujet = "actualités politiques"
        return ("recherche_web", {"requete": sujet})

    # 7. Recherche web générale (sport, faits, météo, etc.)
    mots_cles_recherche = [
        "cherche sur internet", "cherche sur le web", "météo", "meteo",
        "qui a gagné", "qui a gagne", "vainqueur",
        "résultat du match", "resultat du match", "grand prix", "championnat", "score"
    ]
    if any(k in t for k in mots_cles_recherche):
        req = re.sub(r'^(?:cherche sur internet|cherche sur le web|sur le web)\s*', '', texte, flags=re.I).strip()
        return ("recherche_web", {"requete": req if req else texte})

    # 8. Détection ultra-rapide des conversations courantes (PAS BESOIN D'ANALYSEUR LLM !)
    mots_cles_conversation = [
        "bonjour", "salut", "hey", "coucou", "hello", "bonsoir",
        "comment vas-tu", "comment tu vas", "ça va", "tu vas bien", "la forme",
        "qui es-tu", "qui est tu", "présente-toi", "presente-toi", "ton nom", "que peux-tu faire",
        "merci", "super", "d'accord", "ok", "parfait", "au revoir", "bye", "à plus",
        "raconte", "blague", "histoire", "poème", "poeme", "aide-moi", "explique",
        "pourquoi", "qu'est-ce que", "c'est quoi", "conseil", "donne-moi", "traduis"
    ]
    if any(k in t for k in mots_cles_conversation):
        return ("discuter", {})

    return (None, {})

def choisir_action(texte):
    """Sélectionne l'outil approprié ou bascule immédiatement en conversation sans latence."""
    outil_rapide, args_rapides = detecter_action_rapide(texte)
    if outil_rapide:
        if outil_rapide == "discuter":
            return {"action": "discuter"}
        return {"action": "outil", "outil": outil_rapide, "arguments": args_rapides}

    # Fallback uniquement si la demande est ambiguë
    try:
        messages = [
            {"role": "system", "content": PROMPT_ANALYSEUR},
            {"role": "user", "content": texte}
        ]
        reponse = ollama.chat(
            model=MODELE_OLLAMA,
            messages=messages,
            format="json",
            options={"num_thread": 8, "temperature": 0.1, "num_predict": 120}
        )
        data = json.loads(reponse["message"]["content"])
        if isinstance(data, dict):
            if data.get("action") == "outil" and data.get("outil") in OUTILS:
                return data
            for k in OUTILS:
                if k in data:
                    args = data[k] if isinstance(data[k], dict) else {"information": str(data[k])}
                    return {"action": "outil", "outil": k, "arguments": args}
    except Exception:
        pass

    return {"action": "discuter"}

def formater_resultat_outil(nom_outil, resultat):
    """Nettoie le résultat d'un outil pour l'IA (supprime les URLs pour forcer une réponse directe)."""
    if nom_outil == "recherche_web" and isinstance(resultat, list):
        lignes = []
        for r in resultat[:3]: # Limité à 3 pour réduire drastiquement la latence de traitement
            if isinstance(r, dict):
                titre = r.get("titre", "")
                extrait = r.get("extrait", "")
                date_art = r.get("date", "")
                if extrait:
                    prefixe = f"[{date_art[:10]}] " if date_art else ""
                    lignes.append(f"• {prefixe}{titre} : {extrait}")
        return "\n".join(lignes) if lignes else "Aucun résultat trouvé sur le web."
    return json.dumps(resultat, ensure_ascii=False, default=str)

def construire_messages_llm(texte, historique, resultat_outil=None, nom_outil=None, langue=None):
    """Construit un contexte compact, percutant et bilingue (FR/EN) pour un temps de réponse instantané."""
    memoire = lire_memoire()
    profil_info = memoire.get("profil", {})
    souvenirs_info = memoire.get("souvenirs", [])
    date_jour = datetime.datetime.now().strftime("%d/%m/%Y")

    lang = langue or detecter_langue_texte(texte)

    if lang == "en":
        systeme = f"""You are MAVERICK (your name is Maverick), the user's high-tech holographic AI assistant, inspired by JARVIS.
Current Date: {date_jour}.
Always reply in natural, concise, sharp and reliable English.
User: {profil_info.get('nom', 'Boss')} ({profil_info.get('ville', 'Dakar')}).
Saved memories: {souvenirs_info}

CORE RULES:
1. STRICT TRUTH: Never invent events, deaths or fake facts.
2. Address the user with respect as 'Boss' or 'Sir'.
3. Give direct, complete, articulate answers. Do not include URLs or web links.
"""
    else:
        systeme = f"""Tu es MAVERICK (ton nom est Maverick), l'assistant personnel holographique IA de l'utilisateur, inspiré de JARVIS.
Date : {date_jour}.
Réponds TOUJOURS en français dans un style direct, dynamique, sérieux et fiable.
Utilisateur : {profil_info.get('nom', 'Patron')} ({profil_info.get('ville', 'Dakar')}).
Faits mémorisés : {souvenirs_info}

RÈGLES D'OR :
1. VÉRITÉ STRICTE : N'invente JAMAIS d'événements, d'accidents ou de morts imaginaires (Emmanuel Macron est vivant).
2. Adresse-toi à l'utilisateur avec respect en l'appelant 'Patron'.
3. Pour les actualités, base-toi UNIQUEMENT sur les faits extraits.
4. Sois complet, précis et direct. Ne fournis AUCUN lien ou URL.
"""
    messages = [{"role": "system", "content": systeme}]

    # Limiter aux 4 derniers échanges récents pour accélérer le prompt evaluation (< 1s sur CPU)
    contexte_recent = historique[-4:] if historique else []
    for h in contexte_recent:
        messages.append(h)

    if resultat_outil is not None:
        donnees_propres = formater_resultat_outil(nom_outil, resultat_outil)
        if lang == "en":
            user_content = f"""User request: {texte}

Verified extracted facts:
{donnees_propres}

Present a clear, accurate, complete summary in English."""
        else:
            user_content = f"""Demande : {texte}

Faits vérifiés extraits :
{donnees_propres}

Présente une synthèse complète, claire, vraie et bien formulée."""
    else:
        user_content = texte

    messages.append({"role": "user", "content": user_content})
    return messages

def generer_reponse_stream(texte, historique, resultat_outil=None, nom_outil=None, langue=None):
    """Génère la réponse mot par mot en streaming avec support bilingue pour un affichage et une voix instantanés."""
    messages = construire_messages_llm(texte, historique, resultat_outil, nom_outil, langue)
    try:
        reponse_stream = ollama.chat(
            model=MODELE_OLLAMA,
            messages=messages,
            stream=True,
            options={
                "num_thread": 8,
                "num_predict": 300,
                "temperature": 0.6,
                "top_p": 0.9
            }
        )
        for chunk in reponse_stream:
            yield chunk.get("message", {}).get("content", "")
    except Exception as e:
        yield f"Erreur lors de la génération : {e}"

def generer_reponse(texte, historique, resultat_outil=None, nom_outil=None, langue=None):
    """Génération complète non streamée (pour les interfaces synchrones)."""
    morceaux = []
    for chunk in generer_reponse_stream(texte, historique, resultat_outil, nom_outil, langue):
        morceaux.append(chunk)
    return "".join(morceaux).strip()

def executer_outil(nom, arguments):
    if nom not in OUTILS:
        return "Outil inconnu."
    outil = OUTILS[nom]
    if outil.get("dangerous"):
        print("\n" + "=" * 50)
        print(" ACTION SENSIBLE DEMANDÉE")
        print(f" Outil     : {nom}")
        print(f" Arguments : {json.dumps(arguments, ensure_ascii=False)}")
        print("=" * 50)
        rep = input("Autoriser cette action ? (oui/non) : ").strip().lower()
        if rep != "oui":
            return "Action annulée par l'utilisateur."
    try:
        if isinstance(arguments, dict):
            return outil["fonction"](**arguments)
        return outil["fonction"](arguments)
    except TypeError:
        try:
            return outil["fonction"](*arguments.values())
        except Exception as e:
            return f"Erreur de paramètres : {e}"
    except Exception as e:
        return f"Erreur d'exécution : {e}"

def maverick():
    print("=" * 60)
    print("       MAVERICK — Assistant Personnel Vocal & Texte")
    print(f"       Modèle : {MODELE_OLLAMA} (Ollama Local)")
    print("       Mémoire Permanente : ACTIVÉE")
    print("=" * 60)

    historique = obtenir_contexte_conversations(nombre_messages=6)
    mode_vocal_actif = True

    while True:
        try:
            texte = input("\nToi : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nMAVERICK : À très bientôt !")
            break

        if texte.lower() in ["exit", "quit", "au revoir", "bye"]:
            print("MAVERICK : À très bientôt !")
            if mode_vocal_actif:
                parler("À très bientôt !")
            break

        if not texte:
            continue

        decision = choisir_action(texte)
        reponse = ""
        if decision.get("action") == "outil":
            nom_outil = decision.get("outil")
            args = decision.get("arguments", {})
            res = executer_outil(nom_outil, args)
            reponse = generer_reponse(texte, historique, resultat_outil=res, nom_outil=nom_outil)
        else:
            reponse = generer_reponse(texte, historique)

        print(f"\nMAVERICK : {reponse}")
        if mode_vocal_actif:
            parler(reponse)

if __name__ == "__main__":
    maverick()
