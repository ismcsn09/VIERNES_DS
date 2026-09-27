"""
Control del navegador: abrir páginas y reproducir música — gratis, sin
API keys. Usa yt-dlp solo para BUSCAR (no descarga nada) y abre el
resultado en tu navegador predeterminado para reproducirlo ahí.
"""

import webbrowser


def abrir_url(args: dict) -> str:
    """Abre una URL en el navegador predeterminado."""
    url = args.get("url", "")
    if not url:
        return "No se especificó una URL."
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Abriendo {url}"


def reproducir_musica(args: dict) -> str:
    """Busca una canción/artista en YouTube y abre el primer resultado."""
    consulta = args.get("consulta", "")
    if not consulta:
        return "No se especificó qué canción o artista reproducir."
    try:
        from yt_dlp import YoutubeDL

        opciones = {"quiet": True, "extract_flat": "in_playlist", "default_search": "ytsearch1"}
        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(consulta, download=False)
            entradas = info.get("entries") or [info]
            if not entradas:
                return f"No encontré resultados para {consulta}."
            video_id = entradas[0].get("id")
            url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(url)
            titulo = entradas[0].get("title", consulta)
            return f"Reproduciendo: {titulo}"
    except Exception as e:
        return f"Error al buscar/reproducir música: {e}"


NAVEGADOR_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "abrir_url",
            "description": "Abre una página web en el navegador predeterminado.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reproducir_musica",
            "description": "Busca una canción o artista en YouTube y la reproduce en el navegador.",
            "parameters": {
                "type": "object",
                "properties": {"consulta": {"type": "string"}},
                "required": ["consulta"],
            },
        },
    },
]

NAVEGADOR_TOOL_FUNCTIONS = {
    "abrir_url": abrir_url,
    "reproducir_musica": reproducir_musica,
}