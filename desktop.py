"""
Control básico del escritorio (Windows), gratis y local con pyautogui.

Empieza simple a propósito: abrir aplicaciones, tomar capturas, mover el
mouse/hacer clic en coordenadas, y escribir texto. Evita dejar que el
modelo haga clics "a ciegas" sin que tú veas qué está pasando — por eso
`tomar_captura` existe: úsala para que el modelo "vea" el escritorio antes
de decidir dónde hacer clic.
"""

import os
import subprocess
import time

import pyautogui

TIMEOUT_COMANDO_SEGUNDOS = 30

pyautogui.FAILSAFE = True  # mueve el mouse a una esquina para abortar de emergencia

CAPTURAS_DIR = os.path.join(os.path.expanduser("~"), "jarvis_capturas")
os.makedirs(CAPTURAS_DIR, exist_ok=True)


def abrir_aplicacion(args: dict) -> str:
    """Abre una app de Windows por nombre (ej. 'notepad', 'chrome', 'calc')."""
    nombre = args.get("nombre", "")
    if not nombre:
        return "No se especificó qué aplicación abrir."
    try:
        os.startfile(nombre)
        return f"Abriendo {nombre}."
    except Exception:
        try:
            subprocess.Popen(nombre, shell=True)
            return f"Abriendo {nombre}."
        except Exception as e:
            return f"No pude abrir {nombre}: {e}"


def tomar_captura(_args: dict) -> str:
    """Toma una captura de pantalla y guarda el archivo (devuelve la ruta)."""
    ruta = os.path.join(CAPTURAS_DIR, f"captura_{int(time.time())}.png")
    pyautogui.screenshot(ruta)
    return f"Captura guardada en: {ruta}"


def mover_clic(args: dict) -> str:
    """Mueve el mouse a (x, y) y opcionalmente hace clic."""
    x, y = args.get("x"), args.get("y")
    clic = args.get("clic", True)
    if x is None or y is None:
        return "Faltan coordenadas x, y."
    pyautogui.moveTo(int(x), int(y), duration=0.3)
    if clic:
        pyautogui.click()
    return f"Mouse movido a ({x}, {y}){' y clic hecho' if clic else ''}."


def escribir_texto(args: dict) -> str:
    """Escribe texto en donde esté el foco actual (como si tecleara)."""
    texto = args.get("texto", "")
    if not texto:
        return "No se especificó qué texto escribir."
    pyautogui.write(texto, interval=0.02)
    return f"Texto escrito: {texto[:50]}"


def presionar_tecla(args: dict) -> str:
    """Presiona una tecla o combinación (ej. 'enter', 'ctrl+s')."""
    tecla = args.get("tecla", "")
    if not tecla:
        return "No se especificó qué tecla presionar."
    teclas = tecla.split("+")
    pyautogui.hotkey(*teclas)
    return f"Tecla(s) presionada(s): {tecla}"


def ejecutar_comando(args: dict) -> str:
    """
    Ejecuta un comando de PowerShell directamente en el sistema.

    Esta es la herramienta "comodín": para cualquier acción del escritorio
    que no tenga una función específica arriba (crear/mover/copiar/borrar
    archivos o carpetas, cerrar un programa, ver info del sistema, cambiar
    volumen, etc.), el modelo puede resolverlo con un comando en vez de
    necesitar una función nueva por cada cosa.

    Es poderosa a propósito, así que trae dos límites básicos: un timeout
    para que no se cuelgue esperando, y un tope a la salida que devuelve.
    No hay sandbox: el comando corre con los mismos permisos que tu
    usuario de Windows.
    """
    comando = args.get("comando", "")
    if not comando:
        return "No se especificó qué comando ejecutar."
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_COMANDO_SEGUNDOS,
        )
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        salida = salida.strip()
        return salida[:2000] if salida else "Comando ejecutado sin salida."
    except subprocess.TimeoutExpired:
        return f"El comando tardó más de {TIMEOUT_COMANDO_SEGUNDOS}s y se canceló."
    except Exception as e:
        return f"Error al ejecutar el comando: {e}"


DESKTOP_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "abrir_aplicacion",
            "description": "Abre una aplicación de Windows por nombre.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string"}},
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tomar_captura",
            "description": "Toma una captura de pantalla del escritorio actual.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mover_clic",
            "description": "Mueve el mouse a coordenadas x,y y opcionalmente hace clic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "clic": {"type": "boolean"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escribir_texto",
            "description": "Escribe texto donde esté el foco actual del teclado.",
            "parameters": {
                "type": "object",
                "properties": {"texto": {"type": "string"}},
                "required": ["texto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "presionar_tecla",
            "description": "Presiona una tecla o combinación, ej. 'enter' o 'ctrl+s'.",
            "parameters": {
                "type": "object",
                "properties": {"tecla": {"type": "string"}},
                "required": ["tecla"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_comando",
            "description": (
                "Ejecuta un comando de PowerShell en el sistema. Úsala para "
                "cualquier acción de archivos/sistema que no tenga una "
                "herramienta específica: crear, mover, copiar o borrar "
                "archivos/carpetas, cerrar un programa, ver información del "
                "sistema, cambiar volumen, etc. Es poderosa: puede modificar "
                "o borrar cosas, así que solo úsala para lo que el usuario "
                "pidió concretamente."
            ),
            "parameters": {
                "type": "object",
                "properties": {"comando": {"type": "string"}},
                "required": ["comando"],
            },
        },
    },
]

DESKTOP_TOOL_FUNCTIONS = {
    "abrir_aplicacion": abrir_aplicacion,
    "tomar_captura": tomar_captura,
    "mover_clic": mover_clic,
    "escribir_texto": escribir_texto,
    "presionar_tecla": presionar_tecla,
    "ejecutar_comando": ejecutar_comando,
}