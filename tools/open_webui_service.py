import os
import sys
import time
import subprocess
import threading
import urllib.request

SERVEUR_WEBUI_URL = os.getenv("OPEN_WEBUI_URL", "http://127.0.0.1:8080")
EXECUTABLE_WEBUI = r"C:\Users\LENOVO\.gemini\antigravity\scratch\open-webui\venv\Scripts\open-webui.exe"
EXECUTABLE_OLLAMA = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")

_PROCESS_WEBUI = None

def est_ollama_actif() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/version")
        with urllib.request.urlopen(req, timeout=1.5) as rep:
            return rep.status == 200
    except Exception:
        return False

def demarrer_ollama_si_necessaire():
    if not est_ollama_actif():
        if os.path.exists(EXECUTABLE_OLLAMA):
            try:
                subprocess.Popen([EXECUTABLE_OLLAMA, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2.0)
            except Exception:
                pass

def est_open_webui_actif() -> bool:
    try:
        req = urllib.request.Request(SERVEUR_WEBUI_URL)
        with urllib.request.urlopen(req, timeout=1.5) as rep:
            return rep.status in [200, 301, 302, 307]
    except Exception:
        return False

def demarrer_serveur_open_webui(en_arriere_plan: bool = True):
    global _PROCESS_WEBUI
    if est_open_webui_actif():
        return True

    # 1. Vérifier qu'Ollama est actif
    demarrer_ollama_si_necessaire()

    # 2. Configurer les variables d'environnement pour Open WebUI
    env = os.environ.copy()
    env["OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
    env["WEBUI_AUTH"] = "False" # Accès personnel direct sans login requis
    env["PORT"] = "8080"

    if not os.path.exists(EXECUTABLE_WEBUI):
        return False

    def run_proc():
        global _PROCESS_WEBUI
        try:
            cmd = [EXECUTABLE_WEBUI, "serve", "--port", "8080"]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            _PROCESS_WEBUI = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
        except Exception as e:
            print(f"[OpenWebUI] Erreur au lancement du processus : {e}")

    threading.Thread(target=run_proc, daemon=True).start()

    # Attendre que le serveur réponde (jusqu'à 15 secondes)
    for _ in range(30):
        time.sleep(0.5)
        if est_open_webui_actif():
            return True

    return False
