"""
Definición de herramientas (tools) que Jarvis puede usar.
Cada tool tiene: un schema (para que el modelo sepa cuándo y cómo llamarla)
y una función real en Python que la ejecuta.

Para agregar una herramienta nueva:
1. Escribe la función Python que hace el trabajo.
2. Agrega su schema a TOOLS_SCHEMA.
3. Regístrala en TOOL_FUNCTIONS.
"""

import datetime
import os

from desktop import DESKTOP_TOOLS_SCHEMA, DESKTOP_TOOL_FUNCTIONS
from outlook_web import OUTLOOK_TOOLS_SCHEMA, OUTLOOK_TOOL_FUNCTIONS
from navegador import NAVEGADOR_TOOLS_SCHEMA, NAVEGADOR_TOOL_FUNCTIONS


# ---------- Funciones reales ----------

def get_datetime(_args: dict) -> str:
    ahora = datetime.datetime.now()
    return ahora.strftime("Hoy es %A %d de %B de %Y, son las %H:%M")


def buscar_web(args: dict) -> str:
    """Búsqueda web gratuita usando DuckDuckGo (sin API key)."""
    query = args.get("query", "")
    if not query:
        return "No se especificó una consulta de búsqueda."
    try:
        from ddgs import DDGS
        resultados = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                resultados.append(f"- {r['title']}: {r['body']} ({r['href']})")
        if not resultados:
            return "No se encontraron resultados."
        return "\n".join(resultados)
    except Exception as e:
        return f"Error al buscar en la web: {e}"


def leer_archivo(args: dict) -> str:
    """Lee el contenido de un archivo de texto local."""
    ruta = args.get("path", "")
    if not ruta or not os.path.isfile(ruta):
        return f"No se encontró el archivo: {ruta}"
    try:
        with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
        # Evitar respuestas gigantes
        return contenido[:4000]
    except Exception as e:
        return f"Error al leer el archivo: {e}"


def listar_archivos(args: dict) -> str:
    """Lista archivos de una carpeta local."""
    ruta = args.get("path", ".")
    if not os.path.isdir(ruta):
        return f"No se encontró la carpeta: {ruta}"
    try:
        items = os.listdir(ruta)
        return "\n".join(items) if items else "La carpeta está vacía."
    except Exception as e:
        return f"Error al listar la carpeta: {e}"


# ---------- Schemas (formato function-calling de Ollama/OpenAI) ----------

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Obtiene la fecha y hora actual.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_web",
            "description": "Busca información actual en internet usando DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_archivo",
            "description": "Lee el contenido de un archivo de texto en el sistema local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del archivo"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_archivos",
            "description": "Lista los archivos de una carpeta local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta de la carpeta"}
                },
                "required": [],
            },
        },
    },
]

TOOLS_SCHEMA = TOOLS_SCHEMA + DESKTOP_TOOLS_SCHEMA + OUTLOOK_TOOLS_SCHEMA + NAVEGADOR_TOOLS_SCHEMA

TOOL_FUNCTIONS = {
    "get_datetime": get_datetime,
    "buscar_web": buscar_web,
    "leer_archivo": leer_archivo,
    "listar_archivos": listar_archivos,
    **DESKTOP_TOOL_FUNCTIONS,
    **OUTLOOK_TOOL_FUNCTIONS,
    **NAVEGADOR_TOOL_FUNCTIONS,
}