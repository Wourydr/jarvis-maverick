import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def recherche_web(requete: str):
    """Recherche rapide sur le web avec support spécialisé des actualités en direct."""
    termes_news = ["actu", "info", "nouvelle", "monde", "politique", "guerre", "match", "sport", "président", "senegal", "france"]
    est_demande_actu = any(t in requete.lower() for t in termes_news)

    resultats = []

    # 1. Si actualités : extraction de 3 dépêches clés récentes
    if est_demande_actu:
        try:
            with DDGS() as ddgs:
                news_list = list(ddgs.news(requete, max_results=3))
                for n in news_list:
                    resultats.append({
                        "titre": n.get("title", ""),
                        "date": n.get("date", ""),
                        "extrait": n.get("body", "")
                    })
        except Exception:
            pass

    # 2. Recherche standard si pas de news trouvée
    if not resultats:
        try:
            with DDGS() as ddgs:
                res_texte = list(ddgs.text(requete, max_results=3))
                if not res_texte:
                    res_texte = list(ddgs.text(requete, backend="html", max_results=3))
                for r in res_texte:
                    resultats.append({
                        "titre": r.get("title", ""),
                        "lien": r.get("href", ""),
                        "extrait": r.get("body", "")
                    })
        except Exception as e:
            return f"Erreur de recherche : {e}"

    return resultats

def lire_page(url: str):
    try:
        html = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"}).text
        soupe = BeautifulSoup(html, "html.parser")
        for tag in soupe(["script", "style", "noscript"]):
            tag.decompose()
        return soupe.get_text(" ", strip=True)[:4000]
    except Exception as e:
        return f"Impossible de lire la page : {e}"
