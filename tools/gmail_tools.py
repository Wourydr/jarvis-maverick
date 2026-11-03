import base64
import os
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GMAIL_CREDENTIALS, GMAIL_TOKEN

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

def get_service():
    creds = None
    if os.path.exists(GMAIL_TOKEN):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS):
                raise FileNotFoundError(
                    f"Fichier '{GMAIL_CREDENTIALS}' introuvable. "
                    "Télécharge tes identifiants OAuth Google Cloud et place-les dans le dossier du projet."
                )
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def lire_derniers_mails(nombre: int = 5):
    try:
        service = get_service()
        resultats = service.users().messages().list(userId="me", maxResults=nombre).execute()
        mails = []
        for message in resultats.get("messages", []):
            detail = service.users().messages().get(
                userId="me", id=message["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            entetes = detail["payload"]["headers"]
            infos = {h["name"]: h["value"] for h in entetes}
            mails.append({
                "de": infos.get("From"),
                "sujet": infos.get("Subject"),
                "date": infos.get("Date")
            })
        return mails
    except Exception as e:
        return f"Erreur Gmail : {e}"

def envoyer_mail(destinataire: str, sujet: str, corps: str):
    try:
        message = MIMEText(corps, "plain", "utf-8")
        message["to"] = destinataire
        message["subject"] = sujet
        brut = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service = get_service()
        service.users().messages().send(userId="me", body={"raw": brut}).execute()
        return f"Mail envoyé à {destinataire}."
    except Exception as e:
        return f"Erreur envoi Gmail : {e}"
