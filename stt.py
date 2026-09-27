"""
Voz a texto (STT), 100% local y gratis con faster-whisper.
Graba unos segundos de audio desde el micrófono y lo transcribe.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURACION_SEGUNDOS = 5  # cuánto graba cada vez que escucha

# "small" es notablemente más preciso que "base" en español, y sigue
# corriendo razonablemente rápido en CPU. Si tu PC es muy limitada y se
# siente lento, puedes volver a "base".
_modelo = WhisperModel("small", device="cpu", compute_type="int8")


def _normalizar_audio(audio: np.ndarray) -> np.ndarray:
    """Sube el volumen si el micrófono graba muy bajo (mejora mucho la precisión)."""
    pico = np.max(np.abs(audio))
    if pico > 0:
        audio = audio / pico * 0.9
    return audio


def escuchar() -> str:
    print(f"Escuchando ({DURACION_SEGUNDOS}s)...")
    audio = sd.rec(
        int(DURACION_SEGUNDOS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    audio = np.squeeze(audio)
    audio = _normalizar_audio(audio)

    segments, _ = _modelo.transcribe(
        audio,
        language="es",
        beam_size=5,
        vad_filter=True,  # recorta silencios/ruido antes de transcribir
    )
    texto = " ".join(seg.text for seg in segments).strip()
    return texto