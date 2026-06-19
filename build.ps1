# Build TXT-TRANS one-folder distribution (PyInstaller).
$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Missing venv: $VenvPython"
}

$ModelBin = Join-Path $RepoRoot "models\nllb-200-distilled-600M-ct2\model.bin"
if (-not (Test-Path $ModelBin)) {
    Write-Error "Missing model. Run scripts\setup_model.ps1 first."
}

Set-Location $RepoRoot

Write-Host "==> Ensure PyInstaller and flet_desktop"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install pyinstaller flet-desktop==0.27.6
} else {
    & $VenvPython -m ensurepip --upgrade
    & $VenvPython -m pip install -q pyinstaller flet-desktop==0.27.6
}

Write-Host "==> App icon (image -> gui/assets/icon.ico)"
$iconSource = Join-Path $RepoRoot "image\8P6yIyDS.jpg"
if (Test-Path $iconSource) {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv pip install pillow | Out-Null
    } else {
        & $VenvPython -m pip install -q pillow
    }
    & $VenvPython (Join-Path $RepoRoot "scripts\convert_app_icon.py")
} else {
    Write-Warning "Icon source missing: $iconSource (using existing gui\assets\icon.ico if any)"
}

Write-Host "==> Stage Flet desktop client"
& $VenvPython (Join-Path $RepoRoot "scripts\prepare_flet_client.py")

Write-Host "==> PyInstaller (one-folder)"
& $VenvPython -m PyInstaller --noconfirm --clean txt_trans.spec

$ExePath = Join-Path $RepoRoot "dist\TXT-TRANS\TXT-TRANS.exe"
if (Test-Path $ExePath) {
    $SizeMb = [math]::Round((Get-ChildItem (Join-Path $RepoRoot "dist\TXT-TRANS") -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host "Build OK: $ExePath (folder total $SizeMb MB)"
} else {
    Write-Error "Build failed: $ExePath not found"
}
