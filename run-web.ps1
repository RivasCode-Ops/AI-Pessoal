# Interface web - http://127.0.0.1:8765
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Execute install.ps1 primeiro." -ForegroundColor Red
    exit 1
}
$pip = Join-Path $Root ".venv\Scripts\pip.exe"
& $pip install -q -e "${Root}[web]" 2>$null
Write-Host "AI-Pessoal Web em http://127.0.0.1:8765" -ForegroundColor Cyan
Write-Host "Ctrl+C para parar." -ForegroundColor DarkGray
& $py -m ai_pessoal.web
