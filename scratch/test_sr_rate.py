import speech_recognition as sr
import numpy as np
from scipy.io.wavfile import write
import tempfile
import os

# Generate 1 sec 440Hz beep at 48000Hz
sample_rate = 48000
t = np.linspace(0, 1, sample_rate, False)
tone = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wav_path = f.name
write(wav_path, sample_rate, tone)

r = sr.Recognizer()
with sr.AudioFile(wav_path) as source:
    audio = r.record(source)
    print("Audio recorded successfully, duration:", audio.duration)

try:
    os.remove(wav_path)
except Exception:
    pass
print("Done!")
