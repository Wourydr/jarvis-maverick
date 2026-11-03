import os
from dotenv import load_dotenv

load_dotenv()

NOTION_KEY = os.getenv("NOTION_KEY", "")
GMAIL_CREDENTIALS = os.getenv("GMAIL_CREDENTIALS", "credentials.json")
GMAIL_TOKEN = os.getenv("GMAIL_TOKEN", "token.json")
JARVIS_DATA = os.path.abspath(os.getenv("JARVIS_DATA", "./data"))

DOSSIER_DOCUMENTS = os.path.join(JARVIS_DATA, "documents")
FICHIER_MEMOIRE = os.path.join(JARVIS_DATA, "memoire.json")
FICHIER_CONVERSATIONS = os.path.join(JARVIS_DATA, "conversations.json")

os.makedirs(DOSSIER_DOCUMENTS, exist_ok=True)

MODELE_OLLAMA = "llama3.2"
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
