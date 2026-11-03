import asyncio
import edge_tts
import os

async def generate(text, voice, rate, pitch, fname):
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await c.save(fname)
    print(f"Saved {fname} ({voice}, rate={rate}, pitch={pitch})")

async def main():
    phrase = "À votre écoute, patron. Tous les systèmes de l'armure Iron Man sont opérationnels. En attente de vos instructions."
    
    # 1. JARVIS Paul Bettany style (calm, noble, deep)
    await generate(phrase, "fr-FR-HenriNeural", "-4%", "-3Hz", "test_jarvis_henri.mp3")
    
    # 2. Tony Stark style (charismatic, confident)
    await generate(phrase, "fr-FR-RemyMultilingualNeural", "+0%", "-2Hz", "test_stark_remy.mp3")

    # 3. English JARVIS Paul Bettany
    phrase_en = "At your service, boss. All Iron Man Mark VII tactical systems are online and fully operational."
    await generate(phrase_en, "en-GB-RyanNeural", "-3%", "-2Hz", "test_jarvis_en.mp3")

asyncio.run(main())
