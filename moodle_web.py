"""
Acceso a Moodle vía automatización de navegador (Playwright).

CÓMO EMPEZAR (una sola vez):
    python moodle_web.py

Se abre un Chrome real. Inicia sesión ahí con tu usuario y contraseña, y
cuando veas tu panel (Dashboard/Página principal), vuelve a la terminal y
presiona Enter. La sesión queda guardada en moodle_estado.json.

DETALLE TÉCNICO (por si te lo preguntas): a diferencia de outlook_web.py,
acá NO usamos un perfil de navegador persistente (carpeta), sino un
archivo de "storage state" (cookies exportadas). La cookie de sesión de
este Moodle es de las que Chromium borra al cerrar el navegador
completamente, así que un perfil persistente no la conserva entre
ejecuciones — pero exportar las cookies a un archivo sí funciona, porque
no depende de que el navegador siga "vivo".

NOTA sobre la detección de tareas: busco enlaces cuya URL apunte a una
actividad (/mod/assign/, /mod/quiz/, etc.), que es estable entre
instalaciones de Moodle aunque el tema visual cambie. Si tu Moodle no
devuelve nada, dime qué ves tú en la página y lo ajustamos.
"""

import os
import re

from playwright.sync_api import sync_playwright

ESTADO_PATH = os.path.join(os.path.dirname(__file__), "moodle_estado.json")
MOODLE_URL = "https://domingosavio.esemtia.net/moodle/my/"

PATRON_TAREA = re.compile(r"/mod/assign/view\.php\?id=(\d+)")

# Frases que indican que una tarea YA fue entregada (en español e inglés,
# por si el idioma de la cuenta varía). Si en tu Moodle usa otro texto,
# dime cuál aparece y lo agregamos aquí.
FRASES_YA_ENTREGADA = [
    "enviado para calificación",
    "calificado",
    "submitted for grading",
    "graded",
]

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _pagina_requiere_login(page) -> bool:
    return "login" in page.url.lower()


def login_manual():
    """Corre esto una vez para iniciar sesión con tu cuenta (ver docstring)."""
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False)
        contexto = navegador.new_context(
            viewport={"width": 1280, "height": 900}, user_agent=_USER_AGENT
        )
        page = contexto.new_page()
        page.goto(MOODLE_URL)
        print("Inicia sesión en la ventana que se abrió.")
        print("Cuando veas tu panel de Moodle, vuelve aquí y presiona Enter.")
        input()
        contexto.storage_state(path=ESTADO_PATH)
        navegador.close()
    print("Sesión guardada. Ya puedes cerrar esto y usar Viernes normalmente.")


def ver_tareas(_args: dict) -> str:
    """Busca tareas/actividades en el panel de Moodle."""
    if not os.path.exists(ESTADO_PATH):
        return (
            "No hay sesión guardada de Moodle. Corre 'python moodle_web.py' "
            "una vez para iniciar sesión manualmente."
        )

    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True)
            contexto = navegador.new_context(
                storage_state=ESTADO_PATH,
                viewport={"width": 1280, "height": 900},
                user_agent=_USER_AGENT,
            )
            page = contexto.new_page()
            page.goto(MOODLE_URL, timeout=30000)

            if _pagina_requiere_login(page):
                navegador.close()
                return (
                    "La sesión de Moodle guardada ya venció. Corre "
                    "'python moodle_web.py' de nuevo para volver a iniciar sesión."
                )

            page.wait_for_load_state("networkidle", timeout=15000)
            enlaces = page.locator("a[href*='/mod/assign/view.php']").all()

            vistos_ids = set()
            candidatos = []  # (id, titulo, href)
            for enlace in enlaces:
                href = enlace.get_attribute("href") or ""
                m = PATRON_TAREA.search(href)
                if not m:
                    continue
                id_tarea = m.group(1)
                if id_tarea in vistos_ids:
                    continue
                vistos_ids.add(id_tarea)
                titulo = (enlace.inner_text() or "").strip() or f"Tarea {id_tarea}"
                candidatos.append((id_tarea, titulo, href))

            pendientes = []
            # Entra a cada tarea (hasta un tope) para ver si ya se entregó.
            for _id_tarea, titulo, href in candidatos[:20]:
                try:
                    pagina_tarea = contexto.new_page()
                    pagina_tarea.goto(href, timeout=15000)
                    pagina_tarea.wait_for_load_state("networkidle", timeout=10000)
                    contenido = pagina_tarea.locator("body").inner_text().lower()
                    pagina_tarea.close()
                except Exception:
                    continue

                ya_entregada = any(f in contenido for f in FRASES_YA_ENTREGADA)
                if not ya_entregada:
                    pendientes.append(f"- {titulo}")

            navegador.close()

        if not candidatos:
            return (
                "No encontré tareas en el panel de Moodle. Puede que esta "
                "institución arme el panel distinto a lo esperado — dime "
                "qué ves tú en la página y lo ajustamos."
            )
        if not pendientes:
            return "No tienes tareas pendientes por entregar."
        return "\n".join(pendientes)
    except Exception as e:
        return f"Error al leer Moodle: {e}"


MOODLE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "ver_tareas",
            "description": "Revisa las tareas y actividades pendientes en el panel de Moodle.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

MOODLE_TOOL_FUNCTIONS = {
    "ver_tareas": ver_tareas,
}


if __name__ == "__main__":
    login_manual()