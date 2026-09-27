"""
Activación por palabra de voz ("Viernes"), en vez de aplausos.

Reutiliza el mismo motor de transcripción (faster-whisper) que ya usa el
resto del programa: escucha en bloques cortos y revisa si el texto
transcrito contiene la palabra clave de activación. Se compara solo por
la palabra clave (no una frase completa), así es más tolerante a
variaciones y ruido, a costa de que baste con decir "Viernes" en
cualquier frase. Se eligió "Viernes" en vez de "Jarvis" porque Whisper
en español reconoce mucho mejor palabras que ya existen en español.
"""

PALABRA_CLAVE = "viernes"

_MAPA_ACENTOS = str.maketrans("áéíóúñ", "aeioun")


def _normalizar(texto: str) -> str:
    return texto.strip().lower().translate(_MAPA_ACENTOS)


def _contiene_frase_activacion(texto: str) -> bool:
    return PALABRA_CLAVE in _normalizar(texto)


def esperar_frase_activacion(escuchar_fn) -> None:
    """Bloquea hasta escuchar la palabra clave. escuchar_fn es stt.escuchar."""
    print('En espera... (di algo con "Viernes" para activar)')
    while True:
        texto = escuchar_fn()
        if texto and _contiene_frase_activacion(texto):
            return