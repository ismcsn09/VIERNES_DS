"""
Estado compartido entre el loop principal (voz o texto) y la interfaz web:
la transcripción de la conversación, el estado actual ("En espera" /
"Despierto"), y la instancia de Jarvis, para que tanto el micrófono como
la interfaz web puedan hablarle al mismo asistente (con el mismo
historial de conversación).
"""

import threading

_lock = threading.Lock()
_transcripcion = []
_estado_actual = "Iniciando..."

jarvis = None            # se asigna en main.py al arrancar
jarvis_lock = threading.Lock()  # evita que voz y web le hablen a la vez


def agregar_mensaje(quien: str, texto: str):
    with _lock:
        _transcripcion.append({"quien": quien, "texto": texto})


def obtener_transcripcion():
    with _lock:
        return list(_transcripcion)


def set_estado(nuevo: str):
    global _estado_actual
    with _lock:
        _estado_actual = nuevo


def obtener_estado() -> str:
    with _lock:
        return _estado_actual