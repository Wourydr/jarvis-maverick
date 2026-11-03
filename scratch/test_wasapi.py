import sounddevice as sd
import numpy as np

# Find WASAPI input device
wasapi_dev = None
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0 and 'wasapi' in sd.query_hostapis(d['hostapi'])['name'].lower():
        if 'intel' in d['name'].lower() or 'microphone' in d['name'].lower():
            wasapi_dev = i
            print(f"Found WASAPI mic: device {i} -> {d['name']}")
            break

if wasapi_dev is None:
    print("No WASAPI device found")
else:
    info = sd.query_devices(wasapi_dev)
    sr = int(info['default_samplerate'])
    print(f"Recording 2s at {sr}Hz...")
    audio = sd.rec(int(2 * sr), samplerate=sr, channels=min(2, info['max_input_channels']), device=wasapi_dev, dtype='float32')
    sd.wait()
    max_val = np.max(np.abs(audio))
    mean_val = np.mean(np.abs(audio))
    print(f"Recorded! Max float32 amplitude: {max_val:.6f}, Mean: {mean_val:.6f}")
