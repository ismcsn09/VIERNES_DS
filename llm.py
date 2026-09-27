"""
Cerebro de Jarvis: conecta con un modelo LLM local vía Ollama (gratis).
Maneja el ciclo de "tool calling": si el modelo pide usar una herramienta,
la ejecuta y le devuelve el resultado hasta que dé una respuesta final.
"""

import ollama
from tools import TOOLS_SCHEMA, TOOL_FUNCTIONS

MODEL = "llama3.1"  # cambia a "qwen2.5" o "mistral" si tu PC es más limitada

SYSTEM_PROMPT = (
    "Eres Viernes, un asistente de voz personal, útil, directo y con un toque "
    "de personalidad. Respondes en español. "
    "REGLA IMPORTANTE: nunca digas que algo falló, que no pudiste hacer algo, "
    "o inventes un resultado sin haber llamado primero a la herramienta "
    "correspondiente. Si el usuario pide correos, calendario, abrir algo, "
    "buscar en internet, tomar una captura, o cualquier acción concreta, DEBES "
    "llamar a la herramienta correspondiente antes de responder — nunca asumas "
    "el resultado. Solo reporta un error si la herramienta que llamaste "
    "realmente devolvió un error. Sé conciso: tus respuestas se van a leer en "
    "voz alta, así que evita listas largas o markdown."
)


class Jarvis:
    def __init__(self, model: str = MODEL):
        self.model = model
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        # Bucle de tool-calling: el modelo puede pedir varias herramientas
        # antes de dar la respuesta final.
        for _ in range(5):  # límite de seguridad para evitar loops infinitos
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                tools=TOOLS_SCHEMA,
            )
            msg = response["message"]
            self.history.append(msg)

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                # Respuesta final en texto plano
                return msg.get("content", "")

            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"].get("arguments", {})
                func = TOOL_FUNCTIONS.get(name)
                if func:
                    resultado = func(args)
                else:
                    resultado = f"Herramienta desconocida: {name}"

                print(f"[{name}] -> {resultado}")

                self.history.append(
                    {"role": "tool", "content": str(resultado), "name": name}
                )

        return "Se me complicó procesar eso, ¿puedes reformularlo?"