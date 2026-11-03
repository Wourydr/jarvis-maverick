import os
import re
import queue
import asyncio
import tempfile
import threading
import edge_tts
import pygame
import speech_recognition as sr
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

try:
    import winsound
except ImportError:
    winsound = None

VOIX_FR = os.getenv("MAVERICK_VOIX_FR", "fr-FR-HenriNeural")
VOIX_EN = os.getenv("MAVERICK_VOIX_EN", "en-GB-RyanNeural")
VOIX_ACTIVEE = os.getenv("MAVERICK_PARLE", "true").lower() in ["1", "true", "yes", "oui"]

def jouer_bip_activation():
    """Joue un petit carillon discret à deux tons pour signaler le réveil."""
    if winsound:
        try:
            winsound.Beep(880, 80)
            winsound.Beep(1320, 120)
        except Exception:
            pass

def verifier_mot_declencheur(phrase: str):
    """
    Vérifie si la phrase contient 'Hey Maverick', 'Hey Mav' (en français ou en anglais)
    avec gestion exhaustive de toutes les variantes phonétiques de reconnaissance vocale.
    """
    if not phrase:
        return False, None
    p = phrase.lower().strip()
    
    # Nettoyage de toute la ponctuation en espaces
    p = re.sub(r'[^\w\s]', ' ', p)
    p = re.sub(r'\s+', ' ', p).strip()

    # Variantes phonétiques courantes transcrites par Google Speech
    mots_reveil = [
        'hey mav', 'hé mav', 'he mav', 'eh mav', 'ay mav', 'ey mav', 'ok mav', 'dis mav', 'dit mav',
        'salut mav', 'bonjour mav', 'hi mav', 'hello mav', 'heille mav',
        'hey mave', 'hé mave', 'he mave', 'eh mave', 'mave', 'mav',
        'hey maverick', 'hé maverick', 'he maverick', 'eh maverick', 'maverick', 'maverik',
        'hey marv', 'hé marv', 'hey mark', 'hey max', 'aimable', 'et mav', 'est mav',
        'hey map', 'eh map', 'hey mac', 'hey math', 'hey mat', 'hey man'
    ]

    for mot in mots_reveil:
        # Match au début de la phrase
        pattern_debut = r'^(?:' + re.escape(mot) + r')\b[\s]*(.*)'
        m = re.search(pattern_debut, p)
        if m:
            return True, m.group(1).strip()

        # Match à l'intérieur de la phrase
        pattern_milieu = r'\b(?:' + re.escape(mot) + r')\b[\s]*(.*)'
        m2 = re.search(pattern_milieu, p)
        if m2:
            return True, m2.group(1).strip()

    return False, None

def detecter_langue_texte(texte: str) -> str:
    """Détecte avec précision si un texte est en français ('fr') ou en anglais ('en')."""
    if not texte:
        return "fr"
    t = texte.lower().strip()

    mots_en = {
        'the', 'is', 'are', 'what', 'how', 'who', 'why', 'where', 'when',
        'can', 'could', 'would', 'please', 'tell', 'me', 'my', 'boss', 'sir',
        'good', 'morning', 'hello', 'hi', 'thank', 'thanks', 'weather', 'news',
        'today', 'time', 'file', 'show', 'create', 'remember', 'speak', 'english',
        'understand', 'you', 'your', 'about', 'with', 'from', 'have', 'has'
    }

    mots_fr = {
        'le', 'la', 'les', 'un', 'une', 'des', 'est', 'sont', 'tu', 'vous',
        'comment', 'quoi', 'quel', 'quelle', 'pourquoi', 'où', 'quand', 'peux',
        'pourrais', 'donne', 'moi', 'patron', 'bonjour', 'salut', 'merci',
        'météo', 'actualités', 'aujourd\'hui', 'heure', 'fichier', 'montre',
        'crée', 'rappelle', 'français', 'avec', 'pour', 'dans', 'sur'
    }

    mots_clean = re.findall(r'\b[a-zA-Zàâäéèêëîïôöùûüç]+\b', t)
    tokens = set(mots_clean)

    sc_en = len(tokens.intersection(mots_en))
    sc_fr = len(tokens.intersection(mots_fr))

    if sc_en > sc_fr:
        return "en"
    if sc_fr > sc_en:
        return "fr"
    if any(c in t for c in "éèêëàâùûôîïçœ"):
        return "fr"

    return "fr"

# ========================================================
# PROFILS VOCAUX IRON MAN & J.A.R.V.I.S.
# ========================================================

PROFIL_VOIX_ACTUEL = os.getenv("MAVERICK_PROFIL_VOIX", "jarvis") # 'jarvis' ou 'stark'

def changer_profil_voix(nouveau_profil: str) -> str:
    global PROFIL_VOIX_ACTUEL
    if "stark" in nouveau_profil.lower() or "tony" in nouveau_profil.lower():
        PROFIL_VOIX_ACTUEL = "stark"
    else:
        PROFIL_VOIX_ACTUEL = "jarvis"
    return PROFIL_VOIX_ACTUEL

def obtenir_profil_voix() -> str:
    return PROFIL_VOIX_ACTUEL

def obtenir_parametres_voix(langue: str = None, texte: str = None, profil: str = None):
    """
    Retourne (nom_voix, rate, pitch) calibrés précisément selon le profil :
    1. 'jarvis' : L'IA emblématique de l'armure Iron Man (Paul Bettany / Jean-Philippe Puymartin)
       - Voix posée, calme, distinguée, noble et technologique (pitch -3Hz, cadence -4%)
    2. 'stark' : Tony Stark (Robert Downey Jr. / Bernard Gabay)
       - Voix dynamique, vive, charismatique et assurée
    """
    p = profil or PROFIL_VOIX_ACTUEL
    l = langue
    if not l and texte:
        l = detecter_langue_texte(texte)

    if l == "en":
        if p == "stark":
            # Tony Stark US : charismatique, énergique
            return "en-US-BrianNeural", "+4%", "-1Hz"
        else:
            # J.A.R.V.I.S. UK : Paul Bettany, distingué, noble
            return "en-GB-RyanNeural", "-3%", "-2Hz"
    else:
        if p == "stark":
            # Tony Stark FR : Bernard Gabay style (Remy)
            return "fr-FR-RemyMultilingualNeural", "+2%", "-2Hz"
        else:
            # J.A.R.V.I.S. FR : Jean-Philippe Puymartin style (Henri avec résonance noble)
            return "fr-FR-HenriNeural", "-4%", "-3Hz"

def obtenir_voix(langue: str = None, texte: str = None) -> str:
    voix, _, _ = obtenir_parametres_voix(langue=langue, texte=texte)
    return voix

def nettoyer_texte_pour_voix(texte: str) -> str:
    """Nettoie le texte des balises markdown, puces, emojis et URLs pour une lecture fluide."""
    t = re.sub(r'https?://\S+', '', texte)
    t = re.sub(r'[*_#`~]', '', t)
    t = re.sub(r'\[.*?\]\(.*?\)', '', t)
    t = re.sub(r'^\s*[-•\d+\.]\s*', '', t, flags=re.M)
    t = re.sub(r'[◈Ψ⚡🎙️🧹➤📰🧠🕒🌐]', '', t)
    t = re.sub(r'\n+', '. ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

async def _generer_audio(texte: str, fichier_sortie: str, voix: str = None, rate: str = None, pitch: str = None):
    # Récupérer les paramètres calibrés Iron Man J.A.R.V.I.S.
    if not voix or not rate or not pitch:
        v_def, r_def, p_def = obtenir_parametres_voix(texte=texte)
        voix = voix or v_def
        rate = rate or r_def
        pitch = pitch or p_def

    communicate = edge_tts.Communicate(texte, voix, rate=rate, pitch=pitch, volume="+20%")
    await communicate.save(fichier_sortie)

def parler(texte: str, voix: str = None, langue: str = None, profil: str = None):
    """Prononce l'intégralité du texte à voix haute avec le profil Iron Man / J.A.R.V.I.S. sélectionné."""
    if not VOIX_ACTIVEE:
        return

    texte_propre = nettoyer_texte_pour_voix(texte)
    if not texte_propre:
        return

    voix_cible, rate_cible, pitch_cible = obtenir_parametres_voix(langue=langue, texte=texte_propre, profil=profil)
    if voix:
        voix_cible = voix

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name

        asyncio.run(_generer_audio(texte_propre, temp_path, voix_cible, rate_cible, pitch_cible))

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(15)

        pygame.mixer.music.unload()
    except Exception:
        pass
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

class LecteurVocalFlux:
    """
    Lecteur audio en streaming phrase par phrase avec support bilingue FR/EN
    et calibrage cinématique J.A.R.V.I.S. / Iron Man.
    """
    def __init__(self, voix: str = None, langue: str = None, profil: str = None):
        self.voix = voix
        self.langue = langue
        self.profil = profil
        self.queue_audio = queue.Queue()
        self.stop_event = threading.Event()
        self.thread_lecture = None
        self.actif = VOIX_ACTIVEE
        if self.actif:
            self._demarrer_thread_lecture()

    def _demarrer_thread_lecture(self):
        def loop_audio():
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            while not self.stop_event.is_set():
                try:
                    fichier = self.queue_audio.get(timeout=0.2)
                except queue.Empty:
                    continue

                if fichier is None:
                    break

                try:
                    if not self.stop_event.is_set():
                        pygame.mixer.music.load(fichier)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                            pygame.time.Clock().tick(20)
                        pygame.mixer.music.unload()
                except Exception:
                    pass
                finally:
                    if os.path.exists(fichier):
                        try:
                            os.remove(fichier)
                        except Exception:
                            pass
                    self.queue_audio.task_done()

        self.thread_lecture = threading.Thread(target=loop_audio, daemon=True)
        self.thread_lecture.start()

    def ajouter_phrase(self, phrase: str):
        """Prend une phrase, génère son audio Iron Man en arrière-plan et la place dans la file de lecture."""
        if not self.actif:
            return
        propre = nettoyer_texte_pour_voix(phrase)
        if not propre or len(propre) < 2:
            return

        voix_cible, rate_cible, pitch_cible = obtenir_parametres_voix(langue=self.langue, texte=propre, profil=self.profil)
        if self.voix:
            voix_cible = self.voix

        def synthese_task():
            temp_f = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    temp_f = f.name
                asyncio.run(_generer_audio(propre, temp_f, voix_cible, rate_cible, pitch_cible))
                if not self.stop_event.is_set():
                    self.queue_audio.put(temp_f)
                else:
                    if os.path.exists(temp_f):
                        os.remove(temp_f)
            except Exception:
                if temp_f and os.path.exists(temp_f):
                    try:
                        os.remove(temp_f)
                    except Exception:
                        pass

        threading.Thread(target=synthese_task, daemon=True).start()

    def attendre_fin(self, timeout: float = 40.0):
        if not self.actif:
            return
        self.queue_audio.put(None)
        if self.thread_lecture:
            self.thread_lecture.join(timeout=timeout)

    def arreter(self):
        self.stop_event.set()
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

# ========================================================
# RECONNAISSANCE VOCALE MULTI-CANAL ET OPTIMISATION WASAPI
# ========================================================

_CACHE_PERIPHERIQUE_MICRO = None

def trouver_meilleur_micro():
    """
    Détecte automatiquement le meilleur périphérique microphone pour Windows.
    Donne la priorité absolue à Windows WASAPI (Direct Audio Session)
    pour éviter les bugs d'atténuation MME/DirectSound sur les micros Intel Smart Sound.
    """
    global _CACHE_PERIPHERIQUE_MICRO
    if _CACHE_PERIPHERIQUE_MICRO is not None:
        return _CACHE_PERIPHERIQUE_MICRO

    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        # 1. Priorité : WASAPI avec nom "microphone", "array", "intel" ou "realtek"
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                api_name = hostapis[d['hostapi']]['name'].lower()
                if 'wasapi' in api_name and any(k in d['name'].lower() for k in ['microphone', 'array', 'intel', 'realtek']):
                    sr = int(d['default_samplerate'])
                    ch = min(2, d['max_input_channels'])
                    _CACHE_PERIPHERIQUE_MICRO = (i, sr, ch)
                    return _CACHE_PERIPHERIQUE_MICRO

        # 2. Tout périphérique WASAPI disponible
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                api_name = hostapis[d['hostapi']]['name'].lower()
                if 'wasapi' in api_name:
                    sr = int(d['default_samplerate'])
                    ch = min(2, d['max_input_channels'])
                    _CACHE_PERIPHERIQUE_MICRO = (i, sr, ch)
                    return _CACHE_PERIPHERIQUE_MICRO

        # 3. Fallback sur le microphone par défaut de Windows
        def_in = sd.default.device[0]
        info = sd.query_devices(def_in)
        sr = int(info['default_samplerate'])
        ch = min(2, info['max_input_channels'])
        _CACHE_PERIPHERIQUE_MICRO = (def_in, sr, ch)
        return _CACHE_PERIPHERIQUE_MICRO
    except Exception:
        # Fallback de secours absolu
        _CACHE_PERIPHERIQUE_MICRO = (None, 44100, 1)
        return _CACHE_PERIPHERIQUE_MICRO

def ecouter_microphone(duree_secondes: float = 3.5, frequence: int = None, langue: str = "fr-FR", afficher_logs: bool = False) -> str:
    """
    Enregistre le microphone via le flux WASAPI natif avec :
    1. Normalisation automatique de gain (AGC) pour capturer les voix douces et éloignées.
    2. Filtrage immédiat du silence pur (pour éviter les blocages réseau).
    3. Transcription automatique Google STT avec bascule de sécurité FR / EN.
    """
    dev_id, sample_rate, channels = trouver_meilleur_micro()
    if frequence:
        sample_rate = frequence

    try:
        # Enregistrement brut en float32 haute fidélité
        raw = sd.rec(
            int(duree_secondes * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            device=dev_id,
            dtype='float32'
        )
        sd.wait()

        # Downmix stéréo vers mono si le périphérique fournit 2 canaux
        if channels > 1:
            mono = np.mean(raw, axis=1)
        else:
            mono = raw.flatten()

        max_amp = float(np.max(np.abs(mono)))
        rms = float(np.sqrt(np.mean(mono**2)))

        if afficher_logs:
            print(f"[Micro] Échantillonnage: {sample_rate}Hz, Max amp: {max_amp:.5f}, RMS: {rms:.5f}")

        # Si l'amplitude est quasi-nulle (aucun son / micro muet), on court-circuite pour fluidifier l'interface
        if max_amp < 0.0008:
            return ""

        # Normalisation adaptative du gain (AGC) : amène le pic à 75% du maximum numérique
        facteur_gain = min(150.0, 0.75 / max(max_amp, 0.005))
        boosted = np.clip(mono * facteur_gain, -1.0, 1.0)
        audio_int16 = (boosted * 32767).astype(np.int16)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            fichier_wav = f.name

        write(fichier_wav, sample_rate, audio_int16)

        r = sr.Recognizer()
        r.energy_threshold = 120
        r.dynamic_energy_threshold = False

        texte = ""
        with sr.AudioFile(fichier_wav) as source:
            audio_data = r.record(source)
            try:
                texte = r.recognize_google(audio_data, language=langue)
            except sr.UnknownValueError:
                # Si non reconnu dans la langue demandée, tester immédiatement l'autre langue (FR <-> EN)
                autre_langue = "en-US" if "fr" in langue.lower() else "fr-FR"
                try:
                    texte = r.recognize_google(audio_data, language=autre_langue)
                except Exception:
                    texte = ""
            except Exception as e:
                if afficher_logs:
                    print(f"[Micro] Erreur reconnaissance : {e}")
                texte = ""

        try:
            os.remove(fichier_wav)
        except Exception:
            pass

        return texte.strip()
    except Exception as e:
        if afficher_logs:
            print(f"[Micro] Erreur capture matérielle : {e}")
        return ""
