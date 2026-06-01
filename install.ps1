# AI-Pessoal - setup Windows
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== AI-Pessoal - instalacao ===" -ForegroundColor Cyan

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python 3.11+ nao encontrado. Instale em https://www.python.org/" -ForegroundColor Red
    exit 1
}
& python --version

$venv = Join-Path $Root ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Criando .venv..." -ForegroundColor Yellow
    & python -m venv $venv
}
$pip = Join-Path $venv "Scripts\pip.exe"
$python = Join-Path $venv "Scripts\python.exe"

& $pip install -q -U pip
& $pip install -q -e "${Root}[web,pdf]"

& $python -c "import ai_pessoal; from ai_pessoal.config import load_config; _, d = load_config(); print('Versao:', ai_pessoal.__version__); print('Dados:', d)"

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host ""
    Write-Host "Ollama encontrado." -ForegroundColor Green
    & ollama list 2>$null
    Write-Host "Modelo sugerido: ollama pull qwen2.5:7b" -ForegroundColor Yellow
    Write-Host "Embeddings:     ollama pull nomic-embed-text" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Ollama nao encontrado. Instale em https://ollama.com" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Pronto ===" -ForegroundColor Green
Write-Host "Terminal:  .\run.ps1"
Write-Host "Web UI:    .\run-web.ps1  (http://127.0.0.1:8765)"
