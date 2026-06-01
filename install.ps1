# AI-Pessoal — setup Windows
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== AI-Pessoal — instalacao ===" -ForegroundColor Cyan

# Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python 3.11+ nao encontrado. Instale em https://www.python.org/" -ForegroundColor Red
    exit 1
}
& python --version

# venv
$venv = Join-Path $Root ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Criando .venv..." -ForegroundColor Yellow
    & python -m venv $venv
}
$pip = Join-Path $venv "Scripts\pip.exe"
$python = Join-Path $venv "Scripts\python.exe"

& $pip install -q -U pip
& $pip install -q -e $Root

# config em ~/.ai-pessoal
& $python -c "from ai_pessoal.config import load_config; c, d = load_config(); print('Dados:', d)"

# Ollama
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host "`nOllama encontrado." -ForegroundColor Green
    & ollama list 2>$null
    $model = "qwen2.5:7b"
    Write-Host "`nPara baixar modelo sugerido: ollama pull $model" -ForegroundColor Yellow
} else {
    Write-Host "`nOllama nao encontrado. Instale em https://ollama.com" -ForegroundColor Yellow
    Write-Host "Depois: ollama pull qwen2.5:7b" -ForegroundColor Yellow
}

Write-Host "`n=== Pronto ===" -ForegroundColor Green
Write-Host "Ativar:  .\.venv\Scripts\Activate.ps1"
Write-Host "Rodar:   python -m ai_pessoal"
Write-Host "Ou:      ai-pessoal"
