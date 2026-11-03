from PIL import Image, ImageDraw
import numpy as np

im = Image.open(r'C:\Users\LENOVO\.gemini\antigravity\scratch\jarvis-personnel\ui\assets\hud_theme_blue_hd.jpg')
draw = ImageDraw.Draw(im)

cx, cy = 956, 582
# Test different circle radii to see which matches the center rings
for r, color in [(140, 'red'), (175, 'yellow'), (220, 'green'), (270, 'cyan')]:
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)

im.save(r'C:\Users\LENOVO\.gemini\antigravity\brain\7304c75f-1a46-41d2-902b-0bad3fd477c5\test_cyan_anchors.jpg')
print("Saved anchor test image.")
