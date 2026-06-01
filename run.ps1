# Inicia AI-Pessoal (terminal)
$Root = $PSScriptRoot
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Execute install.ps1 primeiro." -ForegroundColor Red
    exit 1
}
& $py -m ai_pessoal @args
