# Jarvis — asistente de voz local y gratuito

Stack 100% gratis:
- **Cerebro:** [Ollama](https://ollama.com) corriendo un modelo local (Llama 3.1)
- **STT:** faster-whisper (offline)
- **TTS:** pyttsx3 (offline)
- **Búsqueda web:** duckduckgo-search (sin API key)

## 1. Instalar Ollama y descargar el modelo

Descarga Ollama desde https://ollama.com/download (Windows, Mac o Linux).

Luego, en una terminal:

```bash
ollama pull llama3.1
```

Si tu PC es limitada (poca RAM/GPU), usa un modelo más liviano:

```bash
ollama pull qwen2.5:3b
```

Y cambia `MODEL = "llama3.1"` por `MODEL = "qwen2.5:3b"` en `llm.py`.

## 2. Instalar dependencias de Python

Requiere Python 3.10+.

```bash
pip install -r requirements.txt
```

Notas por sistema operativo:
- **Windows:** pyttsx3 usa las voces de Windows (SAPI5) — no necesita nada extra.
- **Mac:** pyttsx3 usa NSSpeechSynthesizer — no necesita nada extra.
- **Linux:** instala `espeak` (`sudo apt install espeak`) para que pyttsx3 tenga voz.

## 3. Probar el cerebro (sin audio todavía)

```bash
python main.py --texto
```

Esto te deja chatear por texto y ver que el tool-calling funciona
(pregúntale "¿qué hora es?" o "busca las noticias de hoy sobre IA").

## 4. Correr en modo voz completo

Asegúrate de tener Ollama corriendo en segundo plano (`ollama serve`,
normalmente arranca solo al instalar), luego:

```bash
python main.py
```

Habla cuando veas "Escuchando...". Por defecto graba 5 segundos por turno
(ajustable en `stt.py`, variable `DURACION_SEGUNDOS`).

## Interfaz web

Cada vez que corres `main.py` (en cualquier modo) se abre automáticamente
un panel en **http://127.0.0.1:8765** — solo accesible desde tu propia
PC, no está expuesto a internet. Ahí ves la conversación en vivo (lo que
hables por voz también aparece ahí) y puedes escribirle mensajes
directamente, sin usar el micrófono.

## Control total del escritorio

Además de las herramientas específicas (abrir apps, capturas, mouse,
teclado), `desktop.py` tiene `ejecutar_comando`, que corre comandos de
PowerShell directamente. Esta es la herramienta "comodín" que le permite
resolver casi cualquier pedido del escritorio sin que tengamos que
programarle una función nueva por cada cosa.

**Esto lo vuelve genuinamente poderoso — y sin red de seguridad.** Puede
crear, mover o borrar archivos, cerrar programas, cambiar configuración,
etc., con los mismos permisos que tu usuario de Windows. No hay
confirmación intermedia antes de ejecutar. Recomendaciones:
- Al principio, pídele cosas concretas y de bajo riesgo para ver cómo se
  comporta, antes de darle instrucciones abiertas tipo "organiza mi
  escritorio" o "limpia mis archivos".
- Evita pedirle acciones destructivas irreversibles (borrar carpetas
  grandes, desinstalar programas) hasta que confíes en cómo interpreta
  tus pedidos.
- Si en algún momento quieres quitarle este poder y dejarlo solo con las
  herramientas específicas, borra `ejecutar_comando` de
  `DESKTOP_TOOLS_SCHEMA` y `DESKTOP_TOOL_FUNCTIONS` en `desktop.py`.

## Configurar acceso a Moodle (una sola vez)

Mismo patrón que Outlook: sesión de navegador guardada, sin API ni claves.

```bash
python moodle_web.py
```

Se abre un Chrome real en `https://domingosavio.esemtia.net/moodle/my/`.
Inicia sesión con tu usuario y contraseña, y cuando veas tu panel, vuelve
a la terminal y presiona Enter. Desde ahí, pídele a Viernes "revisa mis
tareas de Moodle".

Si en algún momento el mensaje dice que la sesión "venció", solo hay que
repetir `python moodle_web.py` para renovarla (las sesiones web caducan
después de un tiempo, es normal).

Como cada Moodle se ve distinto según la institución, la detección busca
enlaces a actividades por su URL (`/mod/assign/`, `/mod/quiz/`, etc.) en
vez de depender del diseño visual — es más robusto, pero si tu panel está
armado muy distinto y no encuentra nada, dime qué ves tú en la página
(¿tiene una sección de "línea de tiempo" o "próximas actividades"?) y
ajustamos el selector juntos.

## Cómo agregar nuevas capacidades

Todo lo que Jarvis "puede hacer" vive en `tools.py`. Para agregar una
herramienta nueva (ej. mandar un correo, controlar un foco, leer tu
calendario):

1. Escribe una función Python que haga el trabajo y devuelva un string.
2. Agrégala a `TOOLS_SCHEMA` con su descripción (así el modelo sabe cuándo
   usarla).
3. Regístrala en `TOOL_FUNCTIONS`.

No hay que tocar `llm.py` ni `main.py` para esto.

## Activación por voz ("Hola Jarvis")

Por defecto, `python main.py` deja a Jarvis "dormido", escuchando en
bloques cortos hasta que digas **"Hola Jarvis"**. Ahí se activa, te dice
"Te escucho" y empieza a procesar lo que digas.

Para desactivarlo, di cualquiera de estas frases mientras está activo:
`chao jarvis`, `apágate`, `duerme`, `hasta luego jarvis`, `detente`,
`adiós jarvis`. Vuelve a quedar dormido esperando el próximo "Hola Jarvis".

Puedes cambiar la frase de activación editando `FRASE_ACTIVACION` en
`wake.py`, y agregar/quitar frases de apagado en `FRASES_DESACTIVAR` en
`main.py`.

Para probar sin depender de la frase de activación (útil mientras ajustas
cosas):

```bash
python main.py --siempre-activo
```

## Música y navegador

`navegador.py` agrega `reproducir_musica` (busca en YouTube con yt-dlp,
sin API key, y abre el primer resultado en tu navegador) y `abrir_url`
(abre cualquier página). Pídele algo como "pon música de X" o "abre
YouTube".

## Control de escritorio

`desktop.py` agrega herramientas básicas: abrir aplicaciones, tomar
capturas de pantalla, mover el mouse/hacer clic, escribir texto y presionar
teclas. Está pensado para crecer con cuidado: si le pides algo como "abre
el bloc de notas y escribe esto", el modelo puede encadenar
`abrir_aplicacion` → `escribir_texto` solo. Para acciones más delicadas
(clics en lugares específicos), pídele primero que tome una captura para
"ver" la pantalla antes de decidir coordenadas.

`pyautogui.FAILSAFE` está activado: si algo se descontrola, mueve el mouse
rápido a la esquina superior izquierda de la pantalla para abortar.

## Configurar acceso a Outlook (una sola vez, gratis, sin Azure)

Microsoft bloqueó en 2026 el registro de apps en Azure para cuentas
personales sin un directorio propio, así que `outlook_web.py` usa un
navegador automatizado (Playwright) en vez de la API oficial. Sigue
funcionando 100% gratis, solo que en vez de un token usa una sesión de
navegador guardada localmente.

1. Instala el navegador que usa Playwright (una sola vez):
   ```bash
   playwright install chromium
   ```
2. Inicia sesión una vez, de forma manual:
   ```bash
   python outlook_web.py
   ```
   Esto abre una ventana de Chrome real. Inicia sesión con tu cuenta (con
   2FA si lo tienes). Cuando veas tu bandeja de entrada, vuelve a la
   terminal y presiona Enter. La sesión queda guardada en
   `outlook_browser_profile/` (no la subas a ningún repositorio público).

Desde ahí, `leer_correos`, `enviar_correo` y `ver_calendario` ya deberían
funcionar. Nota: como depende del diseño de la web de Outlook, si algo
falla probablemente sea un selector que cambió — dímelo con el mensaje de
error exacto y lo ajustamos.

Si en algún momento consigues acceso a Azure (por ejemplo con una cuenta de
trabajo/estudio, o te unes al programa de Visual Studio), dejé también
`outlook_graph.py` listo con la versión vía Microsoft Graph API, que es
más robusta — solo habría que volver a apuntar `tools.py` a ese archivo.

## Mover el proyecto a otra computadora (con Git)

**En tu PC actual (una sola vez):**

```bash
git init
git add .
git commit -m "Viernes"
```

Luego crea un repositorio vacío en GitHub y súbelo:

```bash
git remote add origin https://github.com/TU_USUARIO/viernes.git
git push -u origin main
```

**En la PC nueva (tuya o de alguien más):**

```bash
git clone https://github.com/TU_USUARIO/viernes.git
cd viernes
.\setup.ps1
```

`setup.ps1` crea el entorno virtual, instala todo, y descarga el modelo de
Ollama si ya lo tienes instalado (si no, te avisa qué instalar primero:
Ollama en sí, desde https://ollama.com/download).

Después del script, faltan dos pasos manuales que son específicos de cada
persona/máquina y por eso no se pueden automatizar del todo:

1. `python outlook_web.py` — iniciar sesión de Outlook en esa PC (cada
   máquina necesita su propio login)
2. `python main.py` — correr Viernes

**Importante:** `.gitignore` ya excluye `outlook_browser_profile/` (tu
sesión de Outlook) y el entorno virtual — nunca subas esa carpeta a un
repositorio, ni siquiera privado, porque contiene tu sesión iniciada.

**Si es la PC de otra persona:** va a necesitar su propia cuenta de
Outlook (inicia sesión con la suya en el paso 1) y bajar su propio modelo
de Ollama. Además, `abrir_aplicacion` y `ejecutar_comando` en `desktop.py`
usan `os.startfile` y PowerShell, que son específicos de **Windows** — si
alguien quiere correrlo en Mac/Linux, esas dos herramientas necesitarían
adaptarse (avísame si llega ese caso y las ajustamos).

## Próximos pasos sugeridos

- Reemplazar pyttsx3 por **Piper** para voces mucho más naturales (sigue
  siendo gratis y local).
- Agregar wake word ("Hey Jarvis") con **Porcupine** (tiene tier gratuito)
  para no tener que correr el script manualmente cada vez.
- Integrar **Home Assistant** (gratis, self-hosted) como herramienta para
  domótica real.
- Agregar herramientas de correo/calendario usando las APIs gratuitas de
  Google (con cuota gratuita generosa para uso personal).