import sys
sys.path.insert(0, r"C:\Users\LENOVO\.gemini\antigravity\scratch\jarvis-personnel")

from tools.open_webui_service import demarrer_serveur_open_webui, est_open_webui_actif, SERVEUR_WEBUI_URL

print("Démarrage du serveur Open WebUI...")
ok = demarrer_serveur_open_webui()
print(f"Statut Open WebUI: {ok} -> URL: {SERVEUR_WEBUI_URL}")
print(f"Est actif: {est_open_webui_actif()}")
