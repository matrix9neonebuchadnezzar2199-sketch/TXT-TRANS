# Start TXT-TRANS GUI with repo venv Python.
$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$MainPy = Join-Path $RepoRoot "gui\main.py"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Missing venv. Run scripts\setup_model.ps1 first."
}

& $VenvPython $MainPy @args
