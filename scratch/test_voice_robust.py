import sounddevice as sd
import numpy as np
import speech_recognition as sr
from scipy.io.wavfile import write
import tempfile
import os

_DEVICE_INFO_CACHE = None

def obtenir_meilleur_peripherique():
    global _DEVICE_INFO_CACHE
    if _DEVICE_INFO_CACHE is not None:
        return _DEVICE_INFO_CACHE

    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    
    # 1. Recherche WASAPI en priorité pour Windows 10/11
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = hostapis[d['hostapi']]['name'].lower()
            if 'wasapi' in api_name and any(k in d['name'].lower() for k in ['microphone', 'array', 'intel', 'realtek']):
                sr = int(d['default_samplerate'])
                ch = min(2, d['max_input_channels'])
                _DEVICE_INFO_CACHE = (i, sr, ch)
                print(f"[Micro] WASAPI optimal sélectionné: ID {i} ({d['name']}), {sr}Hz, {ch}ch")
                return _DEVICE_INFO_CACHE

    # 2. Tout micro WASAPI
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            api_name = hostapis[d['hostapi']]['name'].lower()
            if 'wasapi' in api_name:
                sr = int(d['default_samplerate'])
                ch = min(2, d['max_input_channels'])
                _DEVICE_INFO_CACHE = (i, sr, ch)
                print(f"[Micro] WASAPI générique sélectionné: ID {i} ({d['name']}), {sr}Hz, {ch}ch")
                return _DEVICE_INFO_CACHE

    # 3. Fallback standard
    def_in = sd.default.device[0]
    info = sd.query_devices(def_in)
    sr = int(info['default_samplerate'])
    ch = min(2, info['max_input_channels'])
    _DEVICE_INFO_CACHE = (def_in, sr, ch)
    print(f"[Micro] Fallback standard sélectionné: ID {def_in} ({info['name']}), {sr}Hz, {ch}ch")
    return _DEVICE_INFO_CACHE

dev_id, rate, channels = obtenir_meilleur_peripherique()
print("Microphone sélectionné avec succès:", dev_id, rate, channels)
