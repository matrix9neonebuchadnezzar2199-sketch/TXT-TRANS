# Download and convert NLLB-200-distilled-600M to CTranslate2 int8 for offline use.
$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot | Split-Path -Parent
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$ModelDir = Join-Path $RepoRoot "models\nllb-200-distilled-600M-ct2"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python 3.12 venv..."
    Set-Location $RepoRoot
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv python install 3.12
        uv venv --python 3.12 .venv
    } else {
        py -3.12 -m venv .venv
    }
}

Set-Location $RepoRoot
Write-Host "==> Installing dependencies"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install -r requirements.txt
} else {
    & $VenvPython -m ensurepip --upgrade
    & $VenvPython -m pip install -r requirements.txt
}

if (Test-Path (Join-Path $ModelDir "model.bin")) {
    Write-Host "Model already present: $ModelDir"
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $ModelDir) | Out-Null

Write-Host "==> Converting facebook/nllb-200-distilled-600M to CTranslate2 int8"
Write-Host "    (first run downloads ~2.4GB from Hugging Face)"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv pip install torch --index-url https://download.pytorch.org/whl/cpu
    uv pip install "ctranslate2>=4.5.0" "transformers>=4.40.0" sentencepiece
} else {
    & $VenvPython -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
    & $VenvPython -m pip install -q "ctranslate2>=4.5.0" "transformers>=4.40.0" sentencepiece
}

$Converter = Join-Path $RepoRoot ".venv\Scripts\ct2-transformers-converter.exe"
if (-not (Test-Path $Converter)) {
  Write-Error "ct2-transformers-converter not found in venv"
}

& $Converter `
  --model facebook/nllb-200-distilled-600M `
  --output_dir $ModelDir `
  --quantization int8 `
  --force

if (-not (Test-Path (Join-Path $ModelDir "model.bin"))) {
    Write-Error "Conversion failed: model.bin not found in $ModelDir"
}

Write-Host "==> Saving tokenizer files for offline use"
& $VenvPython -c @"
from pathlib import Path
from transformers import AutoTokenizer
model_dir = Path(r'$ModelDir')
tokenizer = AutoTokenizer.from_pretrained('facebook/nllb-200-distilled-600M')
tokenizer.save_pretrained(model_dir)
print('Tokenizer saved to', model_dir)
"@

if (-not (Test-Path (Join-Path $ModelDir "tokenizer_config.json"))) {
    Write-Error "Tokenizer save failed"
}

Write-Host "Model ready: $ModelDir"
$SizeMb = [math]::Round((Get-ChildItem $ModelDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Write-Host "Total size: $SizeMb MB"
