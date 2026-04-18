$ErrorActionPreference = "Stop"

Write-Host "Setting up Acuifero 4 + Vigia MVP..."
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$env:UV_CACHE_DIR = Join-Path $BackendDir ".uv-cache"

Write-Host "[1] Setting up backend..."
Push-Location $BackendDir
if (!(Test-Path ".venv")) {
    uv venv
    uv pip install -e .[dev]
} else {
    Write-Host "Backend virtualenv already exists. Skipping reinstall."
}
Pop-Location

Write-Host "[2] Setting up frontend..."
Push-Location $FrontendDir
npm install --legacy-peer-deps
Pop-Location

Write-Host "[3] Seeding data if missing..."
if (!(Test-Path (Join-Path $BackendDir "data\edge.db"))) {
    & $BackendPython (Join-Path $BackendDir "src\acuifero_vigia\scripts\seed.py")
}

Write-Host "Setup complete."
