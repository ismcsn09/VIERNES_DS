"""
Interfaz web local para Viernes: un panel simple que corre en
http://127.0.0.1:8765 mientras main.py está abierto. Muestra la
conversación en vivo (lo que se dice por voz también aparece aquí) y deja
escribirle mensajes directamente desde el navegador, sin usar el
micrófono — útil para probar rápido o cuando no quieres hablar en voz
alta.

No expone nada a internet: solo escucha en 127.0.0.1 (tu propia máquina).
"""

import threading
import webbrowser

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import estado

app = FastAPI()

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Viernes</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0d12;
    --bg-panel: #10141bcc;
    --accent: #ff8a34;
    --accent-dim: #7a4218;
    --accent-2: #35e0c0;
    --text: #eef1f5;
    --text-muted: #626c78;
    --line: #1c222c;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: 'Space Grotesk', system-ui, sans-serif;
    display: flex; flex-direction: column; align-items: center;
    padding: env(safe-area-inset-top,0) 0 env(safe-area-inset-bottom,0);
    overflow: hidden;
  }

  /* ---------- HUD circular ---------- */
  .hud-wrap { position: relative; width: min(46vh, 360px); aspect-ratio: 1;
              margin: 4vh auto 1.5vh; flex-shrink: 0; }
  .hud-wrap svg { position: absolute; inset: 0; width: 100%; height: 100%; }

  .ring-outer { fill: none; stroke: var(--accent-dim); stroke-width: 1.5; opacity: .8; }
  .ring-ticks line { stroke: var(--accent); stroke-width: 2; opacity: .55; }
  .ring-arc { fill: none; stroke: var(--accent); stroke-width: 5;
              stroke-linecap: round; filter: drop-shadow(0 0 6px var(--accent)); }
  .ring-arc-2 { fill: none; stroke: var(--accent-2); stroke-width: 2.5;
                stroke-linecap: round; opacity: .85; }
  .rotor { transform-origin: 50% 50%; animation: girar 40s linear infinite; }
  .rotor.activo { animation-duration: 10s; }
  @keyframes girar { to { transform: rotate(360deg); } }

  .glow { position: absolute; inset: 18%; border-radius: 50%;
          background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
          opacity: .12; filter: blur(6px); animation: latido 3.2s ease-in-out infinite; }
  .glow.activo { opacity: .28; animation-duration: 1.3s; }
  @keyframes latido { 0%,100% { transform: scale(.94); } 50% { transform: scale(1.04); } }

  .hud-centro { position: absolute; inset: 0; display: flex; flex-direction: column;
                align-items: center; justify-content: center; text-align: center; gap: 6px; }
  .wordmark { font-size: clamp(20px, 4.5vh, 30px); font-weight: 700; letter-spacing: .06em; }
  .estado-txt { font-family: 'IBM Plex Mono', monospace; font-size: 12px;
                letter-spacing: .12em; color: var(--accent); text-transform: uppercase; }
  .estado-txt.idle { color: var(--text-muted); }

  /* ---------- Log / consola ---------- */
  .consola { width: min(560px, 92vw); flex: 1; min-height: 0; display: flex;
             flex-direction: column; background: var(--bg-panel); border: 1px solid var(--line);
             border-radius: 10px; margin-bottom: calc(12px + env(safe-area-inset-bottom,0)); }
  #chat { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex;
          flex-direction: column; gap: 10px; font-family: 'IBM Plex Mono', monospace;
          font-size: 13.5px; line-height: 1.5; }
  .linea { display: flex; gap: 8px; }
  .quien { flex-shrink: 0; opacity: .8; }
  .quien.tu { color: var(--text-muted); }
  .quien.viernes { color: var(--accent); }
  .texto { color: var(--text); white-space: pre-wrap; word-break: break-word; }

  form { display: flex; gap: 8px; padding: 10px; border-top: 1px solid var(--line); }
  form .prompt { font-family: 'IBM Plex Mono', monospace; color: var(--accent);
                 display: flex; align-items: center; padding-left: 4px; }
  input { flex: 1; padding: 10px 8px; border: none; background: transparent;
          color: var(--text); font-family: 'IBM Plex Mono', monospace; font-size: 14px; }
  input:focus { outline: none; }
  button { padding: 8px 16px; border-radius: 6px; border: 1px solid var(--accent-dim);
           background: transparent; color: var(--accent); font-family: 'IBM Plex Mono', monospace;
           font-size: 13px; cursor: pointer; }
  button:hover { background: var(--accent-dim); }
  button:disabled { opacity: .4; cursor: default; }

  @media (prefers-reduced-motion: reduce) {
    .rotor, .glow { animation: none !important; }
  }
</style>
</head>
<body>

  <div class="hud-wrap">
    <svg viewBox="0 0 200 200">
      <circle class="ring-outer" cx="100" cy="100" r="92"/>
      <g class="rotor" id="rotorTicks">
        <g class="ring-ticks" id="ticks"></g>
      </g>
      <g class="rotor activo" id="rotorArc" style="animation-duration:22s">
        <circle class="ring-arc" cx="100" cy="100" r="76"
                stroke-dasharray="120 358" stroke-dashoffset="0"/>
      </g>
      <g class="rotor" id="rotorArc2" style="animation-direction:reverse; animation-duration:30s">
        <circle class="ring-arc-2" cx="100" cy="100" r="64"
                stroke-dasharray="60 342"/>
      </g>
    </svg>
    <div class="glow" id="glow"></div>
    <div class="hud-centro">
      <div class="wordmark">VIERNES</div>
      <div class="estado-txt idle" id="estadoTxt">...</div>
    </div>
  </div>

  <div class="consola">
    <div id="chat"></div>
    <form id="form">
      <span class="prompt">&gt;</span>
      <input id="input" placeholder="Escríbele a Viernes..." autocomplete="off" />
      <button type="submit">Enviar</button>
    </form>
  </div>

<script>
// Dibuja las marcas del anillo exterior (como un dial)
const ticksEl = document.getElementById('ticks');
for (let i = 0; i < 36; i++) {
  const angulo = (i / 36) * 360;
  const largo = i % 3 === 0 ? 10 : 5;
  const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  line.setAttribute('x1', 100);
  line.setAttribute('y1', 8);
  line.setAttribute('x2', 100);
  line.setAttribute('y2', 8 + largo);
  line.setAttribute('transform', `rotate(${angulo} 100 100)`);
  ticksEl.appendChild(line);
}

const chatEl = document.getElementById('chat');
const estadoTxtEl = document.getElementById('estadoTxt');
const glowEl = document.getElementById('glow');
const rotorArcEl = document.getElementById('rotorArc');
const formEl = document.getElementById('form');
const inputEl = document.getElementById('input');

let ultimaCantidad = 0;

function render(transcripcion) {
  if (transcripcion.length === ultimaCantidad) return;
  chatEl.innerHTML = '';
  for (const m of transcripcion) {
    const linea = document.createElement('div');
    linea.className = 'linea';
    const quien = document.createElement('span');
    quien.className = 'quien ' + (m.quien === 'tu' ? 'tu' : 'viernes');
    quien.textContent = (m.quien === 'tu' ? 'TÚ' : 'VIERNES') + ' >';
    const texto = document.createElement('span');
    texto.className = 'texto';
    texto.textContent = m.texto;
    linea.appendChild(quien);
    linea.appendChild(texto);
    chatEl.appendChild(linea);
  }
  ultimaCantidad = transcripcion.length;
  chatEl.scrollTop = chatEl.scrollHeight;
}

function aplicarEstado(estado) {
  estadoTxtEl.textContent = estado;
  const activo = /despierto|escuchando|procesando/i.test(estado);
  estadoTxtEl.classList.toggle('idle', !activo);
  glowEl.classList.toggle('activo', activo);
  rotorArcEl.style.animationDuration = activo ? '6s' : '22s';
}

async function refrescar() {
  try {
    const r = await fetch('/estado');
    const data = await r.json();
    aplicarEstado(data.estado);
    render(data.transcripcion);
  } catch (e) { /* el servidor puede tardar un poco en arrancar */ }
}

setInterval(refrescar, 1000);
refrescar();

formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const texto = inputEl.value.trim();
  if (!texto) return;
  inputEl.value = '';
  inputEl.disabled = true;
  aplicarEstado('Procesando');
  await fetch('/mensaje', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({texto}),
  });
  inputEl.disabled = false;
  inputEl.focus();
  refrescar();
});
</script>
</body>
</html>
"""


class MensajeIn(BaseModel):
    texto: str


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.get("/estado")
def get_estado():
    return {
        "estado": estado.obtener_estado(),
        "transcripcion": estado.obtener_transcripcion(),
    }


@app.post("/mensaje")
def enviar_mensaje(msg: MensajeIn):
    estado.agregar_mensaje("tu", msg.texto)
    if estado.jarvis is None:
        return {"ok": False, "error": "Viernes no está listo todavía."}
    with estado.jarvis_lock:
        respuesta = estado.jarvis.chat(msg.texto)
    estado.agregar_mensaje("viernes", respuesta)
    return {"ok": True, "respuesta": respuesta}


def iniciar_en_hilo(puerto: int = 8765):
    """Arranca la interfaz web en un hilo aparte y abre el navegador."""

    def _correr():
        uvicorn.run(app, host="127.0.0.1", port=puerto, log_level="warning")

    hilo = threading.Thread(target=_correr, daemon=True)
    hilo.start()
    webbrowser.open(f"http://127.0.0.1:{puerto}")