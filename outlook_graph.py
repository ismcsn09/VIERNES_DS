"""
Acceso a Outlook (correo y calendario) vía Microsoft Graph API — gratis,
oficial, para cuentas personales de Microsoft (outlook.com/hotmail).

Requiere un registro de app UNA sola vez en Azure (gratis, ver README.md,
sección "Configurar acceso a Outlook"). Necesitas el CLIENT_ID que te da
ese registro; pégalo abajo.

La primera vez que uses una herramienta de correo, va a pedirte que abras
una URL en el navegador e ingreses un código (esto es "device code flow" de
Microsoft, no necesita contraseña guardada en ningún lado). Después de eso,
el token queda cacheado localmente en token_cache.json y no te lo vuelve a
pedir mientras el token siga vigente.
"""

import json
import os

import msal
import requests

CLIENT_ID = "PEGA_AQUI_TU_CLIENT_ID"  # <-- del registro en Azure
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.Read", "Mail.Send", "Calendars.Read"]
CACHE_PATH = os.path.join(os.path.dirname(__file__), "token_cache.json")
GRAPH_URL = "https://graph.microsoft.com/v1.0"


def _cargar_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_PATH):
        cache.deserialize(open(CACHE_PATH, "r").read())
    return cache


def _guardar_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_PATH, "w") as f:
            f.write(cache.serialize())


def _obtener_token() -> str:
    if CLIENT_ID == "PEGA_AQUI_TU_CLIENT_ID":
        raise RuntimeError(
            "Falta configurar CLIENT_ID en outlook_graph.py. "
            "Sigue el README, sección 'Configurar acceso a Outlook'."
        )

    cache = _cargar_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )

    cuentas = app.get_accounts()
    resultado = None
    if cuentas:
        resultado = app.acquire_token_silent(SCOPES, account=cuentas[0])

    if not resultado:
        flujo = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flujo:
            raise RuntimeError(f"No se pudo iniciar el login: {flujo}")
        print(flujo["message"])  # instrucciones para el usuario
        resultado = app.acquire_token_by_device_flow(flujo)

    _guardar_cache(cache)

    if "access_token" not in resultado:
        raise RuntimeError(f"No se pudo obtener token: {resultado.get('error_description')}")

    return resultado["access_token"]


def _headers():
    token = _obtener_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- Funciones para tools.py ----------

def leer_correos(args: dict) -> str:
    """Lee los correos más recientes de la bandeja de entrada."""
    cantidad = args.get("cantidad", 5)
    try:
        resp = requests.get(
            f"{GRAPH_URL}/me/messages?$top={cantidad}&$select=subject,from,receivedDateTime,bodyPreview",
            headers=_headers(),
        )
        resp.raise_for_status()
        mensajes = resp.json().get("value", [])
        if not mensajes:
            return "No hay correos."
        lineas = []
        for m in mensajes:
            remitente = m.get("from", {}).get("emailAddress", {}).get("name", "?")
            lineas.append(f"- De {remitente}: {m.get('subject')} — {m.get('bodyPreview', '')[:100]}")
        return "\n".join(lineas)
    except Exception as e:
        return f"Error al leer correos: {e}"


def enviar_correo(args: dict) -> str:
    """Envía un correo."""
    destinatario = args.get("destinatario", "")
    asunto = args.get("asunto", "")
    cuerpo = args.get("cuerpo", "")
    if not destinatario or not asunto:
        return "Falta destinatario o asunto."
    payload = {
        "message": {
            "subject": asunto,
            "body": {"contentType": "Text", "content": cuerpo},
            "toRecipients": [{"emailAddress": {"address": destinatario}}],
        }
    }
    try:
        resp = requests.post(f"{GRAPH_URL}/me/sendMail", headers=_headers(), json=payload)
        resp.raise_for_status()
        return f"Correo enviado a {destinatario}."
    except Exception as e:
        return f"Error al enviar correo: {e}"


def ver_calendario(args: dict) -> str:
    """Lista los próximos eventos del calendario."""
    cantidad = args.get("cantidad", 5)
    try:
        resp = requests.get(
            f"{GRAPH_URL}/me/events?$top={cantidad}&$orderby=start/dateTime&$select=subject,start,end",
            headers=_headers(),
        )
        resp.raise_for_status()
        eventos = resp.json().get("value", [])
        if not eventos:
            return "No hay eventos próximos."
        lineas = []
        for ev in eventos:
            inicio = ev.get("start", {}).get("dateTime", "")
            lineas.append(f"- {ev.get('subject')} a las {inicio}")
        return "\n".join(lineas)
    except Exception as e:
        return f"Error al leer el calendario: {e}"


OUTLOOK_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "leer_correos",
            "description": "Lee los correos más recientes de Outlook.",
            "parameters": {
                "type": "object",
                "properties": {"cantidad": {"type": "integer"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_correo",
            "description": "Envía un correo desde Outlook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string"},
                    "asunto": {"type": "string"},
                    "cuerpo": {"type": "string"},
                },
                "required": ["destinatario", "asunto", "cuerpo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ver_calendario",
            "description": "Lista los próximos eventos del calendario de Outlook.",
            "parameters": {
                "type": "object",
                "properties": {"cantidad": {"type": "integer"}},
            },
        },
    },
]

OUTLOOK_TOOL_FUNCTIONS = {
    "leer_correos": leer_correos,
    "enviar_correo": enviar_correo,
    "ver_calendario": ver_calendario,
}
