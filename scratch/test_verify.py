import sys
import os

# Assurer l'import de jarvis-personnel
sys.path.insert(0, r"C:\Users\LENOVO\.gemini\antigravity\scratch\jarvis-personnel")

from tools.voix import trouver_meilleur_micro, verifier_mot_declencheur, detecter_langue_texte

dev = trouver_meilleur_micro()
print("Micro détecté (ID, Rate, Channels):", dev)

tests = [
    "Hey Mav",
    "hé mav quelle heure est-il",
    "he mav",
    "Maverick donne-moi la météo",
    "ok mav",
    "dis mav",
    "hey mave",
    "salut mav",
    "aimable",
    "hey mark",
    "hey mav what time is it"
]

print("\n--- Test des variantes Hey Mav ---")
for t in tests:
    ok, cmd = verifier_mot_declencheur(t)
    print(f"'{t}' -> Détecté: {ok} | Reste commande: '{cmd}'")

assert detecter_langue_texte("What is the weather today?") == "en"
assert detecter_langue_texte("Donne-moi les actualités en France") == "fr"
print("\nValidation linguistique FR / EN: OK")
