"""
Punto de entrada de Viernes.

Modo texto (para probar el cerebro sin lidiar con audio todavía):
    python main.py --texto

Modo voz con activación por la palabra "Viernes" (por defecto):
    python main.py

Modo voz siempre activo, sin esperar la palabra de activación (para pruebas):
    python main.py --siempre-activo

En todos los modos también se abre un panel web en http://127.0.0.1:8765
con la conversación en vivo y una caja para escribirle sin usar el
micrófono.
"""

import argparse

import estado
import ui
from llm import Jarvis

FRASES_DESACTIVAR = {
    "chao jarvis", "chau jarvis", "chao viernes", "chau viernes",
    "apágate", "apagate", "duerme", "duerme viernes",
    "hasta luego viernes", "detente", "para viernes",
    "adiós viernes", "adios viernes",
}


def modo_texto():
    estado.jarvis = Jarvis()
    ui.iniciar_en_hilo()
    estado.set_estado("Despierto (modo texto)")
    print("Jarvis (modo texto). Escribe 'salir' para terminar.\n")
    while True:
        user_text = input("Tú: ").strip()
        if user_text.lower() in {"salir", "exit", "quit"}:
            break
        if not user_text:
            continue
        estado.agregar_mensaje("tu", user_text)
        with estado.jarvis_lock:
            respuesta = estado.jarvis.chat(user_text)
        estado.agregar_mensaje("viernes", respuesta)
        print(f"Jarvis: {respuesta}\n")


def _sesion_activa(hablar, escuchar) -> None:
    """Corre mientras Jarvis está 'despierto', hasta escuchar frase de apagado."""
    estado.set_estado("Despierto")
    hablar("Te escucho.")
    estado.agregar_mensaje("viernes", "Te escucho.")
    while True:
        texto = escuchar()
        if not texto:
            continue

        print(f"Tú: {texto}")
        estado.agregar_mensaje("tu", texto)
        texto_normalizado = texto.strip().lower().rstrip(".!¿?")

        if texto_normalizado in FRASES_DESACTIVAR:
            hablar("Hasta luego.")
            estado.agregar_mensaje("viernes", "Hasta luego.")
            return

        with estado.jarvis_lock:
            respuesta = estado.jarvis.chat(texto)
        print(f"Jarvis: {respuesta}")
        estado.agregar_mensaje("viernes", respuesta)
        hablar(respuesta)


def modo_voz(siempre_activo: bool = False):
    from stt import escuchar
    from tts import hablar
    from wake import esperar_frase_activacion

    estado.jarvis = Jarvis()
    ui.iniciar_en_hilo()
    print("Jarvis listo.\n")

    if siempre_activo:
        _sesion_activa(hablar, escuchar)
        return

    while True:
        try:
            estado.set_estado("En espera")
            esperar_frase_activacion(escuchar)
            _sesion_activa(hablar, escuchar)
        except KeyboardInterrupt:
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--texto", action="store_true", help="Corre en modo texto (sin audio)"
    )
    parser.add_argument(
        "--siempre-activo",
        action="store_true",
        help="Modo voz sin esperar la palabra de activación (para pruebas)",
    )
    args = parser.parse_args()

    if args.texto:
        modo_texto()
    else:
        modo_voz(siempre_activo=args.siempre_activo)