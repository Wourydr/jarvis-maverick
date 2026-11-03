import sys
import os
import time
import threading
import customtkinter as ctk

from jarvis import choisir_action, executer_outil, generer_reponse
from tools.memoire import (
    charger_historique_permanent, sauvegarder_message_permanent,
    obtenir_contexte_conversations, lire_memoire
)
from tools.voix import (
    parler, ecouter_microphone,
    jouer_bip_activation, verifier_mot_declencheur
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MaverickApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MAVERICK — Assistant IA Personnel (Hey Mav + Mémoire)")
        self.geometry("940x730")
        self.minsize(720, 520)

        # État
        self.voix_activee = True
        self.ecoute_continue_activee = True
        self.en_cours_de_traitement = False
        
        # Charger le contexte des discussions passées
        self.historique = obtenir_contexte_conversations(nombre_messages=12)

        self._creer_interface()
        self._charger_discussions_passees()

        # Démarrer l'écouteur d'activation en arrière-plan
        threading.Thread(target=self._boucle_wake_word, daemon=True).start()

    def _creer_interface(self):
        # 1. En-tête supérieur
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#0f172a")
        self.header_frame.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=" MAVERICK",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8"
        )
        self.title_label.pack(side="left", padx=15, pady=12)

        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="● Prêt | Dis « Hey Mav »",
            font=ctk.CTkFont(size=12),
            text_color="#4ade80"
        )
        self.status_label.pack(side="left", padx=5)

        # Bouton Effacer
        self.clear_btn = ctk.CTkButton(
            self.header_frame,
            text=" Effacer",
            width=75,
            height=30,
            fg_color="#334155",
            hover_color="#475569",
            command=self.effacer_vue
        )
        self.clear_btn.pack(side="right", padx=12, pady=12)

        # Bouton Toggle Hey Mav
        self.wake_btn = ctk.CTkButton(
            self.header_frame,
            text="⚡ Hey Mav : ON",
            width=115,
            height=30,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.toggle_wake_word
        )
        self.wake_btn.pack(side="right", padx=4, pady=12)

        # Bouton Toggle Son
        self.mute_btn = ctk.CTkButton(
            self.header_frame,
            text="🔊 Voix : ON",
            width=100,
            height=30,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.toggle_voix
        )
        self.mute_btn.pack(side="right", padx=4, pady=12)

        # 2. Zone de messages (Scrollable)
        self.chat_container = ctk.CTkScrollableFrame(self, fg_color="#020617")
        self.chat_container.pack(fill="both", expand=True, padx=15, pady=(10, 10))

        # 3. Barre de saisie inférieure
        self.input_frame = ctk.CTkFrame(self, height=70, corner_radius=12, fg_color="#0f172a")
        self.input_frame.pack(fill="x", side="bottom", padx=15, pady=(0, 15))

        # Bouton Micro manuel
        self.mic_btn = ctk.CTkButton(
            self.input_frame,
            text="🎙️ Parler",
            width=90,
            height=42,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.declencher_ecoute_vocale
        )
        self.mic_btn.pack(side="left", padx=(10, 8), pady=12)

        # Champ de texte
        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Dis « Hey Mav » ou écris ta question ici...",
            height=42,
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            fg_color="#1e293b",
            border_color="#334155"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5, pady=12)
        self.entry.bind("<Return>", lambda event: self.envoyer_message())

        # Bouton Envoyer
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Envoyer ➤",
            width=95,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.envoyer_message
        )
        self.send_btn.pack(side="right", padx=(8, 10), pady=12)

    def _charger_discussions_passees(self):
        """Recharge l'historique permanent dans l'interface au démarrage."""
        tous_les_messages = charger_historique_permanent()
        if tous_les_messages:
            sep = ctk.CTkLabel(
                self.chat_container,
                text="─── Discussions précédentes rechargées (Mémoire permanente active) ───",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color="#64748b"
            )
            sep.pack(pady=10)

            for msg in tous_les_messages[-15:]:
                role = "Toi" if msg.get("role") == "user" else "MAVERICK"
                date_str = msg.get("date", "")
                self.ajouter_message(role, msg.get("content", ""), badge=date_str if date_str else None)

            self.ajouter_message("MAVERICK", "Ravi de vous retrouver ! Dites simplement « Hey Mav » ou posez votre question.")
        else:
            self.ajouter_message("MAVERICK", "Bonjour ! Je suis MAVERICK. Dites « Hey Mav » ou écrivez votre question pour démarrer.")
            if self.voix_activee:
                threading.Thread(target=parler, args=("Bonjour ! Je suis Maverick. Je suis prêt !",), daemon=True).start()

    def toggle_wake_word(self):
        self.ecoute_continue_activee = not self.ecoute_continue_activee
        if self.ecoute_continue_activee:
            self.wake_btn.configure(text="⚡ Hey Mav : ON", fg_color="#16a34a")
            self.status_label.configure(text="● Prêt | Dis « Hey Mav »", text_color="#4ade80")
        else:
            self.wake_btn.configure(text="⚡ Hey Mav : OFF", fg_color="#64748b")
            self.status_label.configure(text="● Prêt (Mode manuel)", text_color="#94a3b8")

    def toggle_voix(self):
        self.voix_activee = not self.voix_activee
        if self.voix_activee:
            self.mute_btn.configure(text="🔊 Voix : ON", fg_color="#0284c7")
        else:
            self.mute_btn.configure(text="🔇 Voix : OFF", fg_color="#64748b")

    def effacer_vue(self):
        for widget in self.chat_container.winfo_children():
            widget.destroy()
        self.ajouter_message("MAVERICK", "Vue réinitialisée. Mes souvenirs sur le disque restent bien conservés !")

    def ajouter_message(self, emetteur: str, texte: str, badge: str = None):
        is_user = (emetteur.lower() == "toi")

        msg_frame = ctk.CTkFrame(
            self.chat_container,
            fg_color="#1e3a8a" if is_user else "#1e293b",
            corner_radius=12
        )
        msg_frame.pack(fill="x", padx=10, pady=6, anchor="e" if is_user else "w")

        header_text = " Vous" if is_user else " MAVERICK"
        if badge:
            header_text += f" • {badge}"

        author_label = ctk.CTkLabel(
            msg_frame,
            text=header_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd" if is_user else "#38bdf8"
        )
        author_label.pack(anchor="w", padx=14, pady=(8, 2))

        content_label = ctk.CTkLabel(
            msg_frame,
            text=texte,
            font=ctk.CTkFont(size=14),
            text_color="#f8fafc",
            wraplength=760,
            justify="left"
        )
        content_label.pack(anchor="w", padx=14, pady=(0, 10))

        self.after(50, lambda: self.chat_container._parent_canvas.yview_moveto(1.0))

    def _boucle_wake_word(self):
        """Écoute discrètement en arrière-plan pour réagir à 'Hey Mav'."""
        while True:
            if not self.ecoute_continue_activee or self.en_cours_de_traitement:
                time.sleep(0.5)
                continue

            try:
                son = ecouter_microphone(duree_secondes=3, afficher_logs=False)
                if not self.ecoute_continue_activee or self.en_cours_de_traitement or not son:
                    continue

                detecte, commande = verifier_mot_declencheur(son)
                if detecte:
                    jouer_bip_activation()
                    self.status_label.configure(text="● 'Hey Mav' détecté ! Je vous écoute...", text_color="#f59e0b")

                    if commande:
                        # Commande déjà présente dans la phrase prononcée
                        threading.Thread(target=self.traiter_demande, args=(commande,), daemon=True).start()
                    else:
                        # L'utilisateur a juste dit "Hey Mav", on écoute sa question pendant 5s
                        self.status_label.configure(text="● Posez votre question...", text_color="#ef4444")
                        question = ecouter_microphone(duree_secondes=5, afficher_logs=False)
                        if question:
                            threading.Thread(target=self.traiter_demande, args=(question,), daemon=True).start()
                        else:
                            self.status_label.configure(text="● Prêt | Dis « Hey Mav »", text_color="#4ade80")
            except Exception:
                time.sleep(1)

    def declencher_ecoute_vocale(self):
        if self.en_cours_de_traitement:
            return

        def task():
            self.en_cours_de_traitement = True
            self.mic_btn.configure(text=" Écoute...", fg_color="#ea580c")
            self.status_label.configure(text="● Écoute en cours... Parlez maintenant", text_color="#f97316")

            texte = ecouter_microphone(duree_secondes=5)

            self.mic_btn.configure(text="🎙️ Parler", fg_color="#dc2626")

            if texte:
                self.traiter_demande(texte)
            else:
                self.status_label.configure(text="● Prêt | Dis « Hey Mav »", text_color="#4ade80")
                self.en_cours_de_traitement = False

        threading.Thread(target=task, daemon=True).start()

    def envoyer_message(self):
        texte = self.entry.get().strip()
        if not texte or self.en_cours_de_traitement:
            return

        self.entry.delete(0, "end")
        threading.Thread(target=self.traiter_demande, args=(texte,), daemon=True).start()

    def traiter_demande(self, texte: str):
        self.en_cours_de_traitement = True
        self.ajouter_message("Toi", texte)

        self.status_label.configure(text="● Maverick réfléchit...", text_color="#38bdf8")

        badge_outil = None
        reponse_finale = ""

        try:
            decision = choisir_action(texte)

            if decision.get("action") == "outil":
                nom_outil = decision.get("outil")
                arguments = decision.get("arguments", {})
                badge_outil = f"Outil : {nom_outil}"
                self.status_label.configure(text=f"● Action : {nom_outil}...", text_color="#eab308")

                resultat = executer_outil(nom_outil, arguments)

                if nom_outil == "se_souvenir":
                    reponse_finale = str(resultat)
                else:
                    self.status_label.configure(text="● Synthèse en cours...", text_color="#38bdf8")
                    reponse_finale = generer_reponse(texte, self.historique, resultat_outil=resultat, nom_outil=nom_outil)
            else:
                reponse_finale = generer_reponse(texte, self.historique)

        except Exception as e:
            reponse_finale = f"Une erreur s'est produite : {e}"

        # Sauvegarde sur disque (Mémoire permanente)
        sauvegarder_message_permanent("user", texte)
        sauvegarder_message_permanent("assistant", reponse_finale)

        self.historique.append({"role": "user", "content": texte})
        self.historique.append({"role": "assistant", "content": reponse_finale})

        # Affichage
        self.ajouter_message("MAVERICK", reponse_finale, badge=badge_outil)

        # Voix
        if self.voix_activee:
            self.status_label.configure(text="● Maverick parle...", text_color="#a855f7")
            parler(reponse_finale)

        self.status_label.configure(text="● Prêt | Dis « Hey Mav »", text_color="#4ade80")
        self.en_cours_de_traitement = False

if __name__ == "__main__":
    app = MaverickApp()
    app.mainloop()
