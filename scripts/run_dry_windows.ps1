$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

$VenvActivate = Join-Path $ProjectRoot ".venv-win\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    throw "Missing .venv-win. Create it with: py -3 -m venv .venv-win"
}

Write-Host "DRY_RUN=1: real orders are disabled"
Write-Host "Using Windows virtual environment: .venv-win"

. $VenvActivate

$env:DRY_RUN = "1"
$env:OKX_DEMO = "1"
$env:BOT_MODE = "live_loop"

python -m src.bot --live-loop --dry-run --okx-demo
