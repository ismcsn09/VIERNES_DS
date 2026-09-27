"""
Texto a voz (TTS), 100% local y gratis con pyttsx3.
No requiere internet ni API key.

Nota: en Windows, reutilizar la misma instancia del motor entre llamadas
es un bug conocido de pyttsx3 (a veces la segunda vez que hablas se queda
en silencio sin dar error). Por eso aquí se crea un motor NUEVO cada vez
en vez de cachearlo — es un poco menos eficiente, pero mucho más
confiable.
"""

import pyttsx3


def hablar(texto: str):
    if not texto:
        return
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    for voice in engine.getProperty("voices"):
        if "spanish" in voice.name.lower() or "spanish" in voice.id.lower():
            engine.setProperty("voice", voice.id)
            break
    engine.say(texto)
    engine.runAndWait()
    engine.stop()