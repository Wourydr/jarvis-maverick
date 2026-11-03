import sounddevice as sd
import numpy as np
import speech_recognition as sr
from scipy.io.wavfile import write
import tempfile
import os

def trouver_meilleur_peripherique_entree():
    """Trouve automatiquement le périphérique d'entrée optimal (WASAPI en priorité sur Windows)."""
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    
    # 1. Chercher WASAPI en priorité
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = hostapis[d['hostapi']]['name'].lower()
            if 'wasapi' in api_name and ('microphone' in d['name'].lower() or 'array' in d['name'].lower() or 'intel' in d['name'].lower()):
                print(f"[Audio] Sélection WASAPI recommandée : index {i} -> {d['name']}")
                return i, int(d['default_samplerate']), min(2, d['max_input_channels'])
                
    # 2. Chercher n'importe quel micro WASAPI
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = hostapis[d['hostapi']]['name'].lower()
            if 'wasapi' in api_name:
                print(f"[Audio] Sélection WASAPI générique : index {i} -> {d['name']}")
                return i, int(d['default_samplerate']), min(2, d['max_input_channels'])

    # 3. Fallback sur le périphérique par défaut
    default_in = sd.default.device[0]
    info = sd.query_devices(default_in)
    print(f"[Audio] Fallback périphérique par défaut : index {default_in} -> {info['name']}")
    return default_in, int(info['default_samplerate']), min(2, info['max_input_channels'])

dev_id, rate, channels = trouver_meilleur_peripherique_entree()
print(f"Device: {dev_id}, Rate: {rate}, Channels: {channels}")

# Test enregistrement 3 secondes
print("Enregistrement 3 secondes (dites quelque chose ou testez le silence)...")
raw = sd.rec(int(3.0 * rate), samplerate=rate, channels=channels, device=dev_id, dtype='float32')
sd.wait()

# Downmix stéréo -> mono si nécessaire
if channels > 1:
    mono = np.mean(raw, axis=1)
else:
    mono = raw.flatten()

max_val = np.max(np.abs(mono))
rms = np.sqrt(np.mean(mono**2))
print(f"Max abs: {max_val:.6f}, RMS: {rms:.6f}")

# Normalisation intelligente du gain
if max_val > 0.0001:
    cible = 0.75 # Normaliser à 75% du max numérique
    gain = min(150.0, cible / max_val)
    norm = np.clip(mono * gain, -1.0, 1.0)
    audio_int16 = (norm * 32767).astype(np.int16)
    print(f"Gain appliqué: {gain:.2f}x -> Nouveau Max Int16: {np.max(np.abs(audio_int16))}")
else:
    audio_int16 = (mono * 32767).astype(np.int16)
    print("Signal quasi nul.")

# Écriture WAV et test Google STT
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wav_path = f.name

write(wav_path, rate, audio_int16)

r = sr.Recognizer()
r.energy_threshold = 150
r.dynamic_energy_threshold = False

with sr.AudioFile(wav_path) as source:
    audio_data = r.record(source)
    try:
        texte = r.recognize_google(audio_data, language="fr-FR")
        print(f"Transcription réussie (FR) : '{texte}'")
    except sr.UnknownValueError:
        try:
            texte = r.recognize_google(audio_data, language="en-US")
            print(f"Transcription réussie (EN) : '{texte}'")
        except sr.UnknownValueError:
            print("Google n'a détecté aucune parole intelligible (silence ou bruit de fond normal).")
        except Exception as e:
            print("Erreur STT EN:", e)
    except Exception as e:
        print("Erreur STT FR:", e)

try:
    os.remove(wav_path)
except Exception:
    pass
