from PIL import Image, ImageDraw
import numpy as np

im = Image.open(r'C:\Users\LENOVO\.gemini\antigravity\brain\7304c75f-1a46-41d2-902b-0bad3fd477c5\.user_uploaded\media_1793675002338_0328d576.jpg')
arr = np.array(im.convert('L'))

# In 626x386, the bright circular core is located in the center area.
# Let's find coordinates of brightest pixels near center:
y_min, y_max = 100, 280
x_min, x_max = 200, 420
sub = arr[y_min:y_max, x_min:x_max]
brightest = np.argwhere(sub > 240)
if len(brightest) > 0:
    cy = int(np.mean(brightest[:, 0])) + y_min
    cx = int(np.mean(brightest[:, 1])) + x_min
    print(f"Detected circle center: cx={cx}, cy={cy}")
else:
    cx, cy = 313, 193
    print(f"Fallback center: cx={cx}, cy={cy}")

print(f"Ratios: cx_ratio={cx/626:.4f}, cy_ratio={cy/386:.4f}")

# Upscale to HD 1920x1183 (exact ratio 626:386)
hd_w = 1920
hd_h = int(1920 * (386 / 626))
im_hd = im.resize((hd_w, hd_h), Image.Resampling.LANCZOS)
# Enhance contrast and sharpness slightly for high tech look
from PIL import ImageEnhance
im_hd = ImageEnhance.Sharpness(im_hd).enhance(1.4)
im_hd = ImageEnhance.Contrast(im_hd).enhance(1.1)

dest = r'C:\Users\LENOVO\.gemini\antigravity\scratch\jarvis-personnel\ui\assets\hud_theme_blue_hd.jpg'
im_hd.save(dest, quality=95)
print(f"Saved HD wallpaper to {dest} ({hd_w}x{hd_h})")
