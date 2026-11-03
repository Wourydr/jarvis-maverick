from PIL import ImageGrab

screenshot = ImageGrab.grab()
screenshot.save(r"C:\Users\LENOVO\.gemini\antigravity\brain\7304c75f-1a46-41d2-902b-0bad3fd477c5\current_screen.png")
print("Screenshot captured successfully! Size:", screenshot.size)
