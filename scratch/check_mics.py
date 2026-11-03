import sounddevice as sd
import numpy as np

print("Testing all input devices for 1 second:")
for i, dev in enumerate(sd.query_devices()):
    if dev['max_input_channels'] > 0:
        try:
            sr = int(dev['default_samplerate'])
            rec = sd.rec(int(1 * sr), samplerate=sr, channels=min(2, dev['max_input_channels']), device=i, dtype='int16')
            sd.wait()
            m = np.max(np.abs(rec))
            avg = np.mean(np.abs(rec))
            print(f"Device {i:2d} | HostAPI {dev['hostapi']} | Max: {m:5d} | Avg: {avg:.2f} | {dev['name']}")
        except Exception as e:
            print(f"Device {i:2d} | Error: {e} | {dev['name']}")
