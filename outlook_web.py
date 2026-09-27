"""
Acceso a Outlook.com vía automatización de navegador (Playwright) — gratis,
sin necesidad de registrar nada en Azure.

Microsoft bloqueó en 2026 el registro de apps en Azure para cuentas
personales sin un directorio propio, y también mató el login básico de
IMAP. Esta es la alternativa que queda: un navegador real controlado por
código, con tu sesión guardada localmente.

CÓMO EMPEZAR (una sola vez):
    python outlook_web.py

Esto abre una ventana de Chrome de verdad. Inicia sesión ahí (con 2FA si lo
tienes), y cuando veas tu bandeja de entrada, vuelve a la terminal y
presiona Enter. La sesión queda guardada en outlook_browser_profile/ y las
próximas veces ya no te va a pedir login.

NOTA: como depende del diseño web de Outlook, si Microsoft cambia la
interfaz, los selectores de abajo podrían necesitar ajuste. Si algo falla,
corre con headless=False (ver _abrir_contexto) para ver qué está pasando
en pantalla.
"""

import os
import re

from playwright.sync_api import sync_playwright

PERFIL_DIR = os.path.join(os.path.dirname(__file__), "outlook_browser_profile")
OUTLOOK_URL = "https://outlook.live.com/mail/0/"
CALENDARIO_URL = "https://outlook.live.com/calendar/0/view/week"


def _abrir_contexto(headless: bool = True):
    playwright = sync_playwright().start()
    contexto = playwright.chromium.launch_persistent_context(
        PERFIL_DIR, headless=headless, viewport={"width": 1280, "height": 900}
    )
    return playwright, contexto


def _pagina_requiere_login(page) -> bool:
    # Si la URL nos manda a login.live.com, no hay sesión activa.
    return "login.live.com" in page.url or "login.microsoftonline.com" in page.url


def login_manual():
    """Corre esto una vez para iniciar sesión con tu cuenta (ver docstring)."""
    playwright, contexto = _abrir_contexto(headless=False)
    page = contexto.pages[0] if contexto.pages else contexto.new_page()
    page.goto(OUTLOOK_URL)
    print("Inicia sesión en la ventana que se abrió.")
    print("Cuando veas tu bandeja de entrada, vuelve aquí y presiona Enter.")
    input()
    contexto.close()
    playwright.stop()
    print("Sesión guardada. Ya puedes cerrar esto y usar Jarvis normalmente.")


def leer_correos(args: dict) -> str:
    """Lee los correos más recientes de la bandeja de entrada."""
    cantidad = args.get("cantidad", 5)
    playwright = contexto = None
    try:
        playwright, contexto = _abrir_contexto(headless=True)
        page = contexto.new_page()
        page.goto(OUTLOOK_URL, timeout=30000)

        if _pagina_requiere_login(page):
            return (
                "No hay sesión activa de Outlook. Corre 'python outlook_web.py' "
                "una vez para iniciar sesión manualmente."
            )

        page.wait_for_selector('[role="option"]', timeout=15000)
        items = page.locator('[role="option"]').all()[:cantidad]
        lineas = []
        for item in items:
            texto = item.inner_text().replace("\n", " | ")
            lineas.append(f"- {texto[:180]}")
        return "\n".join(lineas) if lineas else "No se encontraron correos."
    except Exception as e:
        return f"Error al leer correos: {e}"
    finally:
        if contexto:
            contexto.close()
        if playwright:
            playwright.stop()


def enviar_correo(args: dict) -> str:
    """Envía un correo desde Outlook."""
    destinatario = args.get("destinatario", "")
    asunto = args.get("asunto", "")
    cuerpo = args.get("cuerpo", "")
    if not destinatario or not asunto:
        return "Falta destinatario o asunto."

    playwright = contexto = None
    try:
        playwright, contexto = _abrir_contexto(headless=True)
        page = contexto.new_page()
        page.goto(OUTLOOK_URL, timeout=30000)

        if _pagina_requiere_login(page):
            return (
                "No hay sesión activa de Outlook. Corre 'python outlook_web.py' "
                "una vez para iniciar sesión manualmente."
            )

        # "New mail" / "Nuevo mensaje" según el idioma de la cuenta
        boton_nuevo = page.get_by_role(
            "button", name=re.compile("nuevo mensaje|new mail", re.I)
        )
        boton_nuevo.click(timeout=15000)

        page.get_by_role("textbox", name=re.compile("para|to", re.I)).fill(destinatario)
        page.keyboard.press("Tab")
        page.get_by_role(
            "textbox", name=re.compile("agregar un asunto|add a subject", re.I)
        ).fill(asunto)
        page.get_by_role(
            "textbox", name=re.compile("cuerpo del mensaje|message body", re.I)
        ).fill(cuerpo)
        page.get_by_role("button", name=re.compile("^enviar$|^send$", re.I)).click(
            timeout=15000
        )
        return f"Correo enviado a {destinatario}."
    except Exception as e:
        return f"Error al enviar correo: {e}"
    finally:
        if contexto:
            contexto.close()
        if playwright:
            playwright.stop()


def ver_calendario(args: dict) -> str:
    """Lista los próximos eventos del calendario (mejor esfuerzo)."""
    playwright = contexto = None
    try:
        playwright, contexto = _abrir_contexto(headless=True)
        page = contexto.new_page()
        page.goto(CALENDARIO_URL, timeout=30000)

        if _pagina_requiere_login(page):
            return (
                "No hay sesión activa de Outlook. Corre 'python outlook_web.py' "
                "una vez para iniciar sesión manualmente."
            )

        page.wait_for_selector('[role="button"][aria-label]', timeout=15000)
        eventos = page.locator('[role="button"][aria-label]').all()
        lineas = []
        for ev in eventos[:15]:
            etiqueta = ev.get_attribute("aria-label") or ""
            # Filtra botones que no parecen eventos (muy cortos)
            if len(etiqueta) > 15:
                lineas.append(f"- {etiqueta[:150]}")
            if len(lineas) >= 5:
                break
        return "\n".join(lineas) if lineas else "No se encontraron eventos."
    except Exception as e:
        return f"Error al leer el calendario: {e}"
    finally:
        if contexto:
            contexto.close()
        if playwright:
            playwright.stop()


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
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

OUTLOOK_TOOL_FUNCTIONS = {
    "leer_correos": leer_correos,
    "enviar_correo": enviar_correo,
    "ver_calendario": ver_calendario,
}


if __name__ == "__main__":
    login_manual()