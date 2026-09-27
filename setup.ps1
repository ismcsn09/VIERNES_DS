<#
Prepara Viernes en una PC nueva: crea el entorno virtual, instala las
dependencias de Python y el navegador de Playwright, y descarga el
modelo de Ollama si lo encuentra instalado.

Uso: desde la carpeta del proyecto, en una terminal de PowerShell:
    .\setup.ps1
#>

Write-Host "== Preparando Viernes ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "No se encontró Python en el PATH." -ForegroundColor Red
    Write-Host "Instálalo desde https://python.org (marca la casilla 'Add python.exe to PATH' al instalar) y vuelve a correr este script."
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual (.venv)..."
    python -m venv .venv
}

Write-Host "Activando entorno virtual..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Instalando dependencias de Python (puede tardar unos minutos)..."
pip install -r requirements.txt

Write-Host "Instalando navegador de Playwright..."
playwright install chromium

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Descargando el modelo de Ollama (si no lo tienes ya)..."
    ollama pull qwen2.5:3b
} else {
    Write-Host ""
    Write-Host "AVISO: no se encontró Ollama instalado." -ForegroundColor Yellow
    Write-Host "Descárgalo de https://ollama.com/download, instálalo, y luego corre:"
    Write-Host "    ollama pull qwen2.5:3b"
}

Write-Host ""
Write-Host "== Listo. Pasos manuales que faltan (una sola vez en esta PC): ==" -ForegroundColor Cyan
Write-Host "  1. python outlook_web.py   -> inicia sesión en Outlook"
Write-Host "  2. python main.py          -> corre Viernes"
