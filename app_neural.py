import os
import sys
import json
import time
import threading
import webview

from jarvis import choisir_action, executer_outil, generer_reponse_stream
from tools.memoire import (
    charger_historique_permanent, sauvegarder_message_permanent,
    obtenir_contexte_conversations
)
from tools.voix import (
    parler, LecteurVocalFlux, ecouter_microphone,
    jouer_bip_activation, verifier_mot_declencheur,
    detecter_langue_texte, obtenir_voix, changer_profil_voix, obtenir_profil_voix
)
from tools.open_webui_service import demarrer_serveur_open_webui, est_open_webui_actif, SERVEUR_WEBUI_URL

class MaverickAPI:
    def __init__(self):
        self.window = None
        self.voix_activee = True
        self.wake_active = True
        self.en_cours = False
        self.langue_preferee = "fr" # 'fr' ou 'en'
        self.theme_actuel = "cyan" # 'cyan' (HUD Matrix Vector) ou 'ironman' (Stark Mark VII)
        self.profil_voix = "jarvis" # 'jarvis' (IA armure Iron Man) ou 'stark' (Tony Stark)
        self.lecteur_actuel = None
        self.historique = obtenir_contexte_conversations(nombre_messages=6)
        
        # Synchronisation stricte de l'accès au microphone physique
        self.mic_lock = threading.Lock()
        self.interrompre_wake = threading.Event()

    def set_window(self, window):
        self.window = window

    def initialiser_ui(self):
        """Appelée par le frontend dès que la page est chargée."""
        tous = charger_historique_permanent()
        recents = tous[-10:] if tous else []
        json_data = json.dumps(recents, ensure_ascii=False)
        self.window.evaluate_js(f"window.chargerHistoriqueUI({json_data});")
        self.window.evaluate_js(f"window.mettreAJourLangueUI('{self.langue_preferee.upper()}');")
        self.window.evaluate_js(f"window.mettreAJourProfilVoixUI('{self.profil_voix.upper()}');")
        self.window.evaluate_js(f"window.appliquerTheme('{self.theme_actuel}');")

    def changer_profil_voix(self, profil: str):
        """Permet de basculer entre la voix J.A.R.V.I.S. (IA d'Iron Man) et Tony Stark."""
        self.profil_voix = changer_profil_voix(profil)
        if self.window:
            self.window.evaluate_js(f"window.mettreAJourProfilVoixUI('{self.profil_voix.upper()}');")

    def changer_theme(self, theme: str):
        """Bascule entre le HUD Cyan Vector et le thème Iron Man Mark VII."""
        self.theme_actuel = "ironman" if "iron" in theme.lower() else "cyan"
        if self.window:
            self.window.evaluate_js(f"window.appliquerTheme('{self.theme_actuel}');")

    def changer_langue(self, langue: str):
        """Permet de basculer entre 'fr' et 'en' via l'interface."""
        self.langue_preferee = "en" if "en" in langue.lower() else "fr"
        self.window.evaluate_js(f"window.mettreAJourLangueUI('{self.langue_preferee.upper()}');")

    def changer_wake_word(self, actif: bool):
        self.wake_active = actif

    def changer_voix(self, actif: bool):
        self.voix_activee = actif
        if not actif and self.lecteur_actuel:
            self.lecteur_actuel.arreter()

    def demarrer_et_obtenir_webui(self):
        """Assure le démarrage du serveur Open WebUI en arrière-plan."""
        threading.Thread(target=demarrer_serveur_open_webui, daemon=True).start()
        return {"actif": True, "url": SERVEUR_WEBUI_URL}

    def activer_micro_manuel(self):
        """Déclenché par le bouton PARLER dans l'interface."""
        if self.en_cours:
            return

        self.en_cours = True
        self.interrompre_wake.set() # Pause immédiate de la boucle wake-word pour libérer le micro

        msg_ecoute = "LISTENING... SPEAK INTO YOUR MIC" if self.langue_preferee == "en" else "🎙️ JE VOUS ÉCOUTE... PARLEZ DANS VOTRE MICRO"
        self.window.evaluate_js(f"window.definirEtat('ecoute', {json.dumps(msg_ecoute)});")

        def task():
            try:
                # Bip discret pour indiquer à l'utilisateur que l'écoute commence
                jouer_bip_activation()

                with self.mic_lock:
                    langue_mic = "en-US" if self.langue_preferee == "en" else "fr-FR"
                    texte = ecouter_microphone(duree_secondes=5.0, langue=langue_mic, afficher_logs=True)

                if texte:
                    self.traiter_demande(texte)
                else:
                    self.en_cours = False
                    self.interrompre_wake.clear()
                    msg_silence = (
                        "⚠️ Aucune parole distincte détectée. Vérifiez que votre micro n'est pas coupé ou parlez plus fort."
                        if self.langue_preferee == "fr" else
                        "⚠️ No distinct speech detected. Please check your mic settings or speak clearly."
                    )
                    self.window.evaluate_js(f"window.ajouterMessage('assistant', {json.dumps(msg_silence)});")
                    msg_standby = "AT YOUR SERVICE // SAY 'HEY MAV'" if self.langue_preferee == "en" else "EN ATTENTE // DITES « HEY MAV »"
                    self.window.evaluate_js(f"window.definirEtat('attente', {json.dumps(msg_standby)});")
            except Exception as e:
                self.en_cours = False
                self.interrompre_wake.clear()
                self.window.evaluate_js(f"window.ajouterMessage('assistant', 'Erreur micro : {e}');")
                self.window.evaluate_js("window.definirEtat('attente');")

        threading.Thread(target=task, daemon=True).start()

    def recevoir_message_texte(self, texte: str):
        """Déclenché par la touche Entrée ou le bouton Envoyer."""
        if self.en_cours:
            return
        threading.Thread(target=self.traiter_demande, args=(texte,), daemon=True).start()

    def traiter_demande(self, texte: str):
        self.en_cours = True
        txt_json = json.dumps(texte, ensure_ascii=False)
        self.window.evaluate_js(f"window.ajouterMessage('user', {txt_json});")
        
        # Déterminer la langue de cette requête
        langue_detectee = detecter_langue_texte(texte)
        langue_rep = "en" if (self.langue_preferee == "en" or langue_detectee == "en") else "fr"

        msg_reflexion = "MAVERICK IS PROCESSING..." if langue_rep == "en" else "MAVERICK ANALYSE..."
        self.window.evaluate_js(f"window.definirEtat('reflexion', '{msg_reflexion}');")

        badge_outil = None
        reponse_complete = ""

        try:
            # 1. Routage instantané (< 1ms)
            decision = choisir_action(texte)
            resultat = None
            nom_outil = None

            if decision.get("action") == "outil":
                nom_outil = decision.get("outil")
                arguments = decision.get("arguments", {})
                
                # Cas particulier : changement de langue ou ouverture Open WebUI
                if nom_outil == "changer_langue":
                    nouvelle_langue = arguments.get("langue", "fr")
                    self.langue_preferee = nouvelle_langue
                    langue_rep = nouvelle_langue
                    self.window.evaluate_js(f"window.mettreAJourLangueUI('{nouvelle_langue.upper()}');")
                    if nouvelle_langue == "en":
                        resultat = "Certainly, boss! I am now operating in English with JARVIS neural synthesis. At your command!"
                    else:
                        resultat = "Bien reçu, patron ! Je repasse en français. À votre écoute !"
                elif nom_outil == "ouvrir_open_webui":
                    self.window.evaluate_js("basculerModeVue('webui');")
                    resultat = "Affichage du Studio Open WebUI dans votre interface Maverick en cours, patron ! Votre serveur Ollama local est connecté." if langue_rep == "fr" else "Opening Open WebUI Studio directly inside Maverick, boss! Local Ollama engine is linked."
                elif nom_outil == "changer_profil_voix":
                    p = arguments.get("profil", "jarvis")
                    self.changer_profil_voix(p)
                    if p == "jarvis":
                        resultat = "Voix de J.A.R.V.I.S. (IA de l'armure d'Iron Man) configurée avec succès, patron ! Tous les systèmes tactiques Mark VII sont à vos ordres." if langue_rep == "fr" else "J.A.R.V.I.S. Iron Man suit neural voice activated, Boss! Mark VII systems online."
                    else:
                        resultat = "Voix de Tony Stark activée, patron ! Paré à décoller !" if langue_rep == "fr" else "Tony Stark profile activated, Boss! Systems ready!"
                else:
                    badge_outil = f"Tool: {nom_outil}" if langue_rep == "en" else f"Outil : {nom_outil}"
                    msg_exec = f"EXECUTING : {nom_outil.upper()}..." if langue_rep == "en" else f"EXÉCUTION : {nom_outil.upper()}..."
                    self.window.evaluate_js(f"window.definirEtat('reflexion', '{msg_exec}');")
                    resultat = executer_outil(nom_outil, arguments)

            # 2. Démarrage de la synthèse vocale en flux (avec la voix de la langue appropriée)
            if self.voix_activee:
                self.lecteur_actuel = LecteurVocalFlux(langue=langue_rep)
                msg_parole = "TRANSMITTING RESPONSE..." if langue_rep == "en" else "MAVERICK TRANSMET LA RÉPONSE..."
                self.window.evaluate_js(f"window.definirEtat('parole', '{msg_parole}');")
            else:
                self.lecteur_actuel = None

            # 3. Création immédiate de la bulle de réponse dans l'interface
            badge_json = json.dumps(badge_outil, ensure_ascii=False) if badge_outil else "null"
            self.window.evaluate_js(f"window.commencerMessageAssistant({badge_json});")

            # 4. Traitement direct pour les commandes immédiates sans LLM (mémorisation, langue, webui, voix)
            if nom_outil in ["se_souvenir", "changer_langue", "ouvrir_open_webui", "changer_profil_voix"]:
                reponse_complete = str(resultat)
                rep_json = json.dumps(reponse_complete, ensure_ascii=False)
                self.window.evaluate_js(f"window.mettreAJourMessageAssistant({rep_json});")
                if self.lecteur_actuel:
                    self.lecteur_actuel.ajouter_phrase(reponse_complete)
                    self.lecteur_actuel.attendre_fin(timeout=10.0)
            else:
                # Streaming en direct des tokens LLM et prononciation progressive phrase par phrase
                accumulateur_phrase = ""
                texte_affiche = ""
                compteur_tokens = 0

                for morceau in generer_reponse_stream(texte, self.historique, resultat_outil=resultat, nom_outil=nom_outil, langue=langue_rep):
                    if not morceau:
                        continue
                    texte_affiche += morceau
                    accumulateur_phrase += morceau
                    compteur_tokens += 1

                    # Rafraîchir l'affichage toutes les 2 unités de texte
                    if compteur_tokens % 2 == 0 or len(morceau) > 4:
                        rep_json = json.dumps(texte_affiche, ensure_ascii=False)
                        self.window.evaluate_js(f"window.mettreAJourMessageAssistant({rep_json});")

                    # Dès qu'une phrase se termine par une ponctuation, on l'envoie à la synthèse vocale
                    if self.lecteur_actuel and any(p in morceau for p in [".", "!", "?", "\n"]):
                        phrase_prete = accumulateur_phrase.strip()
                        if len(phrase_prete) >= 8:
                            accumulateur_phrase = ""
                            self.lecteur_actuel.ajouter_phrase(phrase_prete)

                # Envoyer le reste final de la phrase à prononcer
                if self.lecteur_actuel and accumulateur_phrase.strip():
                    self.lecteur_actuel.ajouter_phrase(accumulateur_phrase.strip())

                # Garantir l'affichage final complet
                reponse_complete = texte_affiche.strip()
                rep_json = json.dumps(reponse_complete, ensure_ascii=False)
                self.window.evaluate_js(f"window.mettreAJourMessageAssistant({rep_json});")

                # Attendre que Maverick termine toute sa diction sans couper la fin
                if self.lecteur_actuel:
                    self.lecteur_actuel.attendre_fin(timeout=45.0)

            self.window.evaluate_js("window.terminerMessageAssistant();")

            # 5. Sauvegarde permanente de la discussion complète
            sauvegarder_message_permanent("user", texte)
            sauvegarder_message_permanent("assistant", reponse_complete)

            self.historique.append({"role": "user", "content": texte})
            self.historique.append({"role": "assistant", "content": reponse_complete})
            if len(self.historique) > 8:
                self.historique = self.historique[-8:]

        except Exception as e:
            err_msg = f"Une erreur s'est produite : {e}"
            self.window.evaluate_js(f"window.mettreAJourMessageAssistant({json.dumps(err_msg)});")
            self.window.evaluate_js("window.terminerMessageAssistant();")

        msg_standby = "AT YOUR SERVICE // SAY 'HEY MAV'" if self.langue_preferee == "en" else "EN ATTENTE // DITES « HEY MAV »"
        self.window.evaluate_js(f"window.definirEtat('attente', '{msg_standby}');")
        self.en_cours = False
        self.interrompre_wake.clear() # Réactivation fluide de l'écoute du mot-clé
        self.lecteur_actuel = None

    def boucle_wake_word(self):
        """
        Écoute en continu avec synchronisation WASAPI pour réveiller Maverick dès qu'il entend 'Hey Mav'.
        Affiche et prononce instantanément : « À votre écoute, patron ! » et prend les commandes.
        """
        while True:
            if not self.wake_active or self.en_cours or self.interrompre_wake.is_set() or not self.window:
                time.sleep(0.25)
                continue

            try:
                langue_ecoute = "en-US" if self.langue_preferee == "en" else "fr-FR"
                
                # Écoute continue protégée par le verrou matériel
                with self.mic_lock:
                    if not self.wake_active or self.en_cours or self.interrompre_wake.is_set():
                        continue
                    son = ecouter_microphone(duree_secondes=2.5, langue=langue_ecoute, afficher_logs=False)

                if not self.wake_active or self.en_cours or self.interrompre_wake.is_set() or not son:
                    continue

                detecte, commande = verifier_mot_declencheur(son)
                if detecte:
                    self.en_cours = True
                    self.interrompre_wake.set()

                    # 1. Remettre la fenêtre au premier plan
                    try:
                        self.window.restore()
                        self.window.show()
                    except Exception:
                        pass

                    # 2. Ouvrir le terminal de discussion
                    self.window.evaluate_js("if (typeof chatVisible !== 'undefined' && !chatVisible) toggleChatPanel();")

                    # 3. Afficher immédiatement la commande vocale de l'utilisateur
                    self.window.evaluate_js("window.ajouterMessage('user', 'Hey Mav !');")

                    # 4. Bip carillon d'activation
                    jouer_bip_activation()

                    # 5. Réponse vocale ET affichage complet : « À votre écoute, patron ! »
                    phrase_reveil = "At your service, boss !" if self.langue_preferee == "en" else "À votre écoute, patron !"
                    self.window.evaluate_js(f"window.ajouterMessage('assistant', {json.dumps(phrase_reveil)});")
                    self.window.evaluate_js(f"window.definirEtat('ecoute', {json.dumps(phrase_reveil.upper())});")

                    if self.voix_activee:
                        parler(phrase_reveil, langue=self.langue_preferee)

                    # 6. Si une commande a été prononcée d'un trait ("Hey Mav donne-moi la météo")
                    if commande and len(commande.strip()) > 3:
                        threading.Thread(target=self.traiter_demande, args=(commande,), daemon=True).start()
                    else:
                        # Sinon, écouter attentivement pendant 6 secondes la demande du patron
                        msg_attente = "LISTENING, BOSS..." if self.langue_preferee == "en" else "JE VOUS ÉCOUTE, PATRON..."
                        self.window.evaluate_js(f"window.definirEtat('ecoute', {json.dumps(msg_attente)});")
                        
                        with self.mic_lock:
                            question = ecouter_microphone(duree_secondes=6.0, langue=langue_ecoute, afficher_logs=True)

                        if question:
                            threading.Thread(target=self.traiter_demande, args=(question,), daemon=True).start()
                        else:
                            msg_standby = "AT YOUR SERVICE // SAY 'HEY MAV'" if self.langue_preferee == "en" else "EN ATTENTE // DITES « HEY MAV »"
                            msg_pas_entendu = "Je n'ai pas capté votre ordre, patron. Je reste en veille." if self.langue_preferee == "fr" else "I didn't catch an order, boss. Standing by."
                            self.window.evaluate_js(f"window.ajouterMessage('assistant', {json.dumps(msg_pas_entendu)});")
                            self.window.evaluate_js(f"window.definirEtat('attente', {json.dumps(msg_standby)});")
                            self.en_cours = False
                            self.interrompre_wake.clear()
            except Exception:
                self.en_cours = False
                self.interrompre_wake.clear()
                time.sleep(1)

def main():
    api = MaverickAPI()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "ui", "index.html")

    window = webview.create_window(
        title="MAVERICK — J.A.R.V.I.S. Holographic Interface",
        url=html_path,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 620),
        background_color="#02050e"
    )
    api.set_window(window)

    threading.Thread(target=api.boucle_wake_word, daemon=True).start()

    webview.start()

if __name__ == "__main__":
    main()
