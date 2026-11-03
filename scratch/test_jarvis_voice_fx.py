import asyncio
import edge_tts
import numpy as np
from scipy.io import wavfile
import tempfile
import os
import pygame

async def generate_speech(texte: str, voix: str, output_path: str):
    # Prosody: rate slightly measured (-3%), pitch steady (+0Hz)
    communicate = edge_tts.Communicate(texte, voix, rate="-3%", pitch="+0Hz")
    await communicate.save(output_path)

def appliquer_filtre_jarvis(input_wav: str, output_wav: str):
    """
    Applique le filtre acoustique légendaire J.A.R.V.I.S. / Iron Man :
    1. Résonance holographique numérique (micro-délai métallique de 18ms)
    2. Filtrage passe-bande Stark (suppression des infra-basses et présence dans les aigus)
    3. Normalisation studio
    """
    samplerate, data = wavfile.read(input_wav)
    
    # Conversion en float32 normalisé [-1.0, 1.0]
    if data.dtype == np.int16:
        signal = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        signal = data.astype(np.float32) / 2147483648.0
    else:
        signal = data.astype(np.float32)

    # Si stéréo, convertir en mono
    if len(signal.shape) > 1:
        signal = np.mean(signal, axis=1)

    # 1. Micro-délai holographique (effet résonance IA Stark)
    # Délai de 20ms avec mélange subtil (18% effet, 82% direct)
    delay_samples = int(samplerate * 0.020)
    reverb_signal = np.zeros(len(signal) + delay_samples, dtype=np.float32)
    reverb_signal[:len(signal)] = signal
    # Injection du premier écho et d'un second micro-écho subtil (flanger / intercom)
    reverb_signal[delay_samples:delay_samples + len(signal)] += signal * 0.22
    delay_2 = int(samplerate * 0.038)
    reverb_signal[delay_2:delay_2 + len(signal)] += signal * 0.10

    # 2. Filtrage léger de présence (subtile amplification des médiums/aigus)
    # Simuler le filtre casque Mark VII / Intercom Stark
    alpha = 0.28
    # Filtre d'accentuation des hautes fréquences (pre-emphasis)
    emphasized = np.append(reverb_signal[0], reverb_signal[1:] - alpha * reverb_signal[:-1])

    # 3. Normalisation propre du pic à -1 dB (0.88)
    peak = np.max(np.abs(emphasized))
    if peak > 0:
        boosted = (emphasized / peak) * 0.88
    else:
        boosted = emphasized

    final_int16 = (np.clip(boosted, -1.0, 1.0) * 32767).astype(np.int16)
    wavfile.write(output_wav, samplerate, final_int16)

async def test_voices():
    phrases = [
        ("fr-FR-RemyMultilingualNeural", "Bonjour patron. Tous les systèmes de l'armure sont opérationnels. À vos ordres."),
        ("fr-FR-HenriNeural", "Bonjour patron. Tous les systèmes de l'armure sont opérationnels. À vos ordres."),
        ("en-GB-RyanNeural", "Good day, boss. All Stark Mark VII systems are online and fully operational at your command.")
    ]

    for voix, phrase in phrases:
        prefix = voix.split("-")[2]
        mp3_path = f"test_{prefix}.mp3"
        wav_raw = f"test_{prefix}_raw.wav"
        wav_fx = f"test_{prefix}_jarvis.wav"

        print(f"\n[Test] Génération voix {voix}...")
        await generate_speech(phrase, voix, mp3_path)
        
        # Convertir mp3 en wav via ffmpeg ou pygame ou soundfile
        import subprocess
        # Test si ffmpeg dispo ou lecture
        print(f"Audio brut généré: {mp3_path}")

asyncio.run(test_voices())
