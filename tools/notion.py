import requests
from config import NOTION_KEY, NOTION_VERSION

def rechercher_notion(requete: str = ""):
    if not NOTION_KEY or NOTION_KEY == "ton_secret_notion":
        return "Erreur Notion : clé NOTION_KEY non configurée dans le fichier .env"
    try:
        r = requests.post(
            "https://api.notion.com/v1/search",
            headers={
                "Authorization": f"Bearer {NOTION_KEY}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json"
            },
            json={"query": requete, "page_size": 10}
        )
        if r.status_code != 200:
            return f"Erreur Notion {r.status_code} : {r.text}"
        pages = []
        for item in r.json().get("results", []):
            titre = "Sans titre"
            if item.get("properties"):
                for prop in item["properties"].values():
                    if prop.get("type") == "title":
                        titres = prop.get("title", [])
                        if titres:
                            titre = titres[0]["plain_text"]
            pages.append({"id": item.get("id"), "titre": titre, "url": item.get("url")})
        return pages
    except Exception as e:
        return f"Erreur de connexion à Notion : {e}"

def lire_page_notion(page_id: str):
    if not NOTION_KEY or NOTION_KEY == "ton_secret_notion":
        return "Erreur Notion : clé NOTION_KEY non configurée dans le fichier .env"
    try:
        r = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers={
                "Authorization": f"Bearer {NOTION_KEY}",
                "Notion-Version": NOTION_VERSION
            }
        )
        if r.status_code != 200:
            return f"Erreur Notion {r.status_code} : {r.text}"
        textes = []
        for bloc in r.json().get("results", []):
            if bloc.get("has_children"):
                continue
            contenu = bloc.get(bloc.get("type"), {})
            for partie in contenu.get("rich_text", []):
                textes.append(partie.get("plain_text", ""))
        return "\n".join(textes)[:10000]
    except Exception as e:
        return f"Erreur de lecture Notion : {e}"
