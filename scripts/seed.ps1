$ErrorActionPreference = "Stop"

Write-Host "Running Seeding Script..."
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

& $BackendPython (Join-Path $BackendDir "src\acuifero_vigia\scripts\seed.py")
Write-Host "Seeding Complete."
